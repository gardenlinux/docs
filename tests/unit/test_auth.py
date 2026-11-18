"""Credential selection, isolation, and read-only authentication preflight."""

import base64
import os
import subprocess
import sys
import urllib.request
from unittest.mock import MagicMock, patch

import pytest

import aggregate
from aggregation.auth import get_token, git_environment, redact_credentials
from aggregation.fetcher import DocsFetcher
from aggregation.github_api import (
    GitHubAPIError,
    _build_request,
    _open_request,
    _SameOriginRedirectHandler,
)
from aggregation.models import RepoConfig
from aggregation.preflight import check_authentication


@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch):
    for variable in (
        "GH_COM_TOKEN",
        "GH_ENTERPRISE_HOST",
        "GH_ENTERPRISE_TOKEN",
        "GITHUB_TOKEN",
        "CI",
        "GIT_CONFIG_COUNT",
        "GIT_TERMINAL_PROMPT",
        "GCM_INTERACTIVE",
    ):
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setenv("GH_ENTERPRISE_HOST", "github.example.com")


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/org/repo", "public"),
        ("https://api.github.com/repos/org/repo", "public"),
        ("https://github.example.com/api/v3/repos/org/repo", "internal"),
        ("https://github.example.com/org/repo", "internal"),
        ("https://github.example.com.attacker.test/repo", ""),
        ("https://github.com.attacker.test/repo", ""),
        ("https://attacker.test/repo", ""),
        ("http://github.com/repo", ""),
        ("https://github.com:444/repo", ""),
        ("https://user@github.com/repo", ""),
    ],
)
def test_exact_host_routing(monkeypatch, url, expected):
    monkeypatch.setenv("GH_COM_TOKEN", " public ")
    monkeypatch.setenv("GH_ENTERPRISE_TOKEN", "internal")
    assert get_token(url) == expected
    assert _build_request(url).get_header("Authorization") == (
        f"Bearer {expected}" if expected else None
    )


def test_legacy_token_is_public_only(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "legacy")
    assert get_token("https://api.github.com") == "legacy"
    assert get_token("https://github.example.com") == ""
    monkeypatch.setenv("GH_COM_TOKEN", "preferred")
    assert get_token("https://api.github.com") == "preferred"


def test_invalid_token_rejected(monkeypatch):
    monkeypatch.setenv("GH_COM_TOKEN", "token\ninjected")
    with pytest.raises(ValueError, match="line breaks"):
        get_token("https://github.com")


@pytest.mark.parametrize("host", ["", "other.example.com"])
def test_enterprise_token_requires_matching_configured_host(monkeypatch, host):
    monkeypatch.setenv("GH_ENTERPRISE_HOST", host)
    monkeypatch.setenv("GH_ENTERPRISE_TOKEN", "internal")
    assert get_token("https://github.example.com/org/repo") == ""
    assert (
        _build_request("https://github.example.com/api/v3/user").get_header(
            "Authorization"
        )
        is None
    )


def test_enterprise_hostname_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("GH_ENTERPRISE_HOST", " GitHub.Example.Com ")
    monkeypatch.setenv("GH_ENTERPRISE_TOKEN", "internal")
    assert get_token("https://GITHUB.EXAMPLE.COM/org/repo") == "internal"


@pytest.mark.parametrize(
    "host",
    [
        "https://github.example.com",
        "user@github.example.com",
        "github.example.com:443",
        "github.example.com/path",
        "github.example.com?query",
        "github.example.com#fragment",
    ],
)
def test_enterprise_host_must_be_a_hostname(monkeypatch, host):
    monkeypatch.setenv("GH_ENTERPRISE_HOST", host)
    with pytest.raises(ValueError, match="must be a hostname"):
        get_token("https://github.example.com/org/repo")


def test_enterprise_configuration_never_overrides_public_token(monkeypatch):
    monkeypatch.setenv("GH_ENTERPRISE_HOST", "github.com")
    monkeypatch.setenv("GH_ENTERPRISE_TOKEN", "internal")
    monkeypatch.setenv("GH_COM_TOKEN", "public")
    assert get_token("https://github.com/org/repo") == "public"


def test_git_credentials_are_ephemeral_and_scoped(monkeypatch):
    monkeypatch.setenv("GH_COM_TOKEN", "public")
    monkeypatch.setenv("GH_ENTERPRISE_TOKEN", "internal")
    monkeypatch.setenv("GIT_TRACE_CURL", "1")
    monkeypatch.setenv("GIT_CURL_VERBOSE", "1")
    url = "https://github.example.com/org/repo"
    env = git_environment(url)
    count = int(env["GIT_CONFIG_COUNT"])
    settings = [
        (env[f"GIT_CONFIG_KEY_{i}"], env[f"GIT_CONFIG_VALUE_{i}"]) for i in range(count)
    ]
    encoded = base64.b64encode(b"x-access-token:internal").decode()
    assert (f"http.{url}.extraHeader", f"Authorization: Basic {encoded}") in settings
    assert (f"http.{url}.extraHeader", "") in settings
    assert (f"http.{url}.followRedirects", "false") in settings
    assert ("credential.helper", "") in settings
    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert env["GCM_INTERACTIVE"] == "Never"
    for variable in (
        "GH_COM_TOKEN",
        "GH_ENTERPRISE_TOKEN",
        "GITHUB_TOKEN",
        "GIT_TRACE_CURL",
        "GIT_CURL_VERBOSE",
    ):
        assert variable not in env
    assert "public" not in str(settings)


def test_existing_git_environment_settings_preserved(monkeypatch):
    monkeypatch.setenv("GH_COM_TOKEN", "public")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "http.sslVerify")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "true")
    env = git_environment("https://github.com/org/repo")
    assert env["GIT_CONFIG_COUNT"] == "5"
    assert env["GIT_CONFIG_KEY_0"] == "http.sslVerify"


def test_git_applies_header_only_to_matching_repository(monkeypatch, tmp_path):
    monkeypatch.setenv("GH_ENTERPRISE_TOKEN", "internal")
    url = "https://github.example.com/org/repo"
    env = git_environment(url)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    encoded = base64.b64encode(b"x-access-token:internal").decode()
    for target, expected in (
        (url + "/info/refs", f"Authorization: Basic {encoded}"),
        ("https://github.example.com/org/other/info/refs", ""),
        ("https://github.com/org/repo/info/refs", ""),
    ):
        result = subprocess.run(
            ["git", "config", "--get-urlmatch", "http.extraHeader", target],
            env=env,
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.stdout.strip() == expected
        assert result.returncode == (0 if expected else 1)


def test_local_credential_manager_preserved_without_token(monkeypatch):
    env = git_environment("https://github.example.com/org/repo")
    assert "GIT_CONFIG_COUNT" not in env
    assert "GIT_TERMINAL_PROMPT" not in env
    monkeypatch.setenv("CI", "true")
    assert (
        git_environment("https://github.example.com/org/repo")["GIT_TERMINAL_PROMPT"]
        == "0"
    )


def test_embedded_credentials_rejected():
    with pytest.raises(ValueError, match="must not contain credentials"):
        git_environment("https://secret@github.example.com/org/repo")


def test_redacts_raw_and_encoded_tokens(monkeypatch):
    monkeypatch.setenv("GH_ENTERPRISE_TOKEN", "internal")
    encoded = base64.b64encode(b"x-access-token:internal").decode()
    assert redact_credentials(f"internal {encoded}") == "[REDACTED] [REDACTED]"


@pytest.mark.parametrize(
    "newurl",
    [
        "https://attacker.test/api",
        "http://api.github.com/api",
        "https://api.github.com:444/api",
        "https://user@api.github.com/api",
    ],
)
def test_api_redirect_does_not_leak_token(newurl):
    req = urllib.request.Request(
        "https://api.github.com/api", headers={"Authorization": "Bearer secret"}
    )
    with pytest.raises(GitHubAPIError, match="cross-origin"):
        _SameOriginRedirectHandler().redirect_request(
            req, None, 302, "Found", {}, newurl
        )


def test_same_origin_api_redirect_allowed():
    req = urllib.request.Request(
        "https://api.github.com/old", headers={"Authorization": "Bearer secret"}
    )
    redirected = _SameOriginRedirectHandler().redirect_request(
        req, None, 302, "Found", {}, "https://api.github.com/new"
    )
    assert redirected.get_header("Authorization") == "Bearer secret"


def test_authenticated_request_uses_safe_opener():
    req = urllib.request.Request(
        "https://api.github.com/api", headers={"Authorization": "Bearer secret"}
    )
    with patch("urllib.request.build_opener") as build:
        _open_request(req)
    assert isinstance(build.call_args.args[0], _SameOriginRedirectHandler)
    build.return_value.open.assert_called_once_with(req, timeout=30)


def test_preflight_requires_internal_token_before_network(monkeypatch):
    monkeypatch.setenv("GH_COM_TOKEN", "public")
    repo = RepoConfig("internal", "https://github.example.com/org/repo", "docs", "main")
    with patch("aggregation.preflight.subprocess.run") as run:
        with pytest.raises(GitHubAPIError, match="Missing GH_ENTERPRISE_TOKEN"):
            check_authentication([repo])
    run.assert_not_called()


def test_preflight_checks_git_and_public_releases(monkeypatch):
    monkeypatch.setenv("GH_COM_TOKEN", "public")
    monkeypatch.setenv("GH_ENTERPRISE_TOKEN", "internal")
    repos = [
        RepoConfig("public", "https://github.com/org/repo", "docs", "main"),
        RepoConfig("internal", "https://github.example.com/org/repo", "docs", "main"),
        RepoConfig("local", "file://../repo", "docs", "main"),
    ]
    with patch("aggregation.preflight.subprocess.run") as run, patch(
        "aggregation.preflight.list_repo_releases", return_value=[{"tag_name": "1"}]
    ) as releases:
        check_authentication(repos)
    assert run.call_count == 2
    for call, repo in zip(run.call_args_list, repos):
        assert call.args[0] == ["git", "ls-remote", "--exit-code", repo.url, "HEAD"]
        assert "internal" not in str(call.args)
        assert call.kwargs["timeout"] == 120
    releases.assert_called_once_with("gardenlinux", "gardenlinux")


def test_preflight_redacts_git_failure(monkeypatch):
    monkeypatch.setenv("GH_COM_TOKEN", "public")
    repo = RepoConfig("source", "https://github.com/org/repo", "docs", "main")
    error = subprocess.CalledProcessError(128, ["git"], stderr="denied public")
    with patch("aggregation.preflight.subprocess.run", side_effect=error):
        with pytest.raises(GitHubAPIError, match="denied \\[REDACTED\\]"):
            check_authentication([repo])


def test_fetcher_supplies_credentials_to_fetch_only(monkeypatch, tmp_path):
    monkeypatch.setenv("GH_ENTERPRISE_TOKEN", "internal")
    repo = RepoConfig("source", "https://github.example.com/org/repo", "docs", "main")
    result = MagicMock(stdout="abc123\n")
    with patch("aggregation.fetcher.subprocess.run", return_value=result) as run:
        success, commit = DocsFetcher(tmp_path)._fetch_remote(repo, tmp_path / "output")
    assert success
    assert commit == "abc123"
    fetch = next(
        call for call in run.call_args_list if call.args[0][:2] == ["git", "fetch"]
    )
    assert "GIT_CONFIG_COUNT" in fetch.kwargs["env"]
    assert "internal" not in str(fetch.args)
    assert all(
        "GIT_CONFIG_COUNT" not in call.kwargs.get("env", {})
        for call in run.call_args_list
        if call != fetch
    )


@pytest.mark.parametrize("failure", [False, True])
def test_cli_preflight_is_read_only_and_respects_single(monkeypatch, tmp_path, failure):
    repos = [
        RepoConfig("public", "https://github.com/org/repo", "docs", "main"),
        RepoConfig("internal", "https://github.example.com/org/repo", "docs", "main"),
    ]
    docs = tmp_path / "docs"
    config = tmp_path / "repos.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "aggregate.py",
            "--check-auth",
            "--repo",
            "internal",
            "--single",
            "--config",
            str(config),
            "--docs-dir",
            str(docs),
            "--update-locks",
        ],
    )
    error = GitHubAPIError("Access denied") if failure else None
    with patch("aggregate.load_config", return_value=repos), patch(
        "aggregate.check_authentication", side_effect=error
    ) as check, patch("aggregate.DocsFetcher") as fetcher, patch(
        "aggregate.save_config"
    ) as save, patch(
        "aggregate.generate_release_docs"
    ) as generate:
        assert aggregate.main() == (1 if failure else 0)
    check.assert_called_once_with([repos[1]])
    fetcher.assert_not_called()
    save.assert_not_called()
    generate.assert_not_called()
    assert not docs.exists()
    assert not config.exists()
