"""Unit tests for aggregation.github_api module."""

import io
import json
import urllib.error
import urllib.request
from http.client import HTTPMessage
from unittest.mock import MagicMock, patch

import pytest

from aggregation.github_api import GitHubAPIError, get_json, list_repo_releases


@pytest.fixture(autouse=True)
def isolate_tokens(monkeypatch):
    for variable in (
        "GH_COM_TOKEN",
        "GH_ENTERPRISE_HOST",
        "GH_ENTERPRISE_TOKEN",
        "GITHUB_TOKEN",
    ):
        monkeypatch.delenv(variable, raising=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(body: bytes, status: int = 200) -> MagicMock:
    """Return a mock context-manager response that yields *body*."""
    resp = MagicMock()
    resp.read.return_value = body
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


def _make_http_error(code: int, headers: dict | None = None) -> urllib.error.HTTPError:
    """Build a :class:`urllib.error.HTTPError` with optional headers."""
    msg = HTTPMessage()
    if headers:
        for key, val in headers.items():
            msg[key] = val
    return urllib.error.HTTPError(
        url="https://api.github.com/test",
        code=code,
        msg=f"HTTP Error {code}",
        hdrs=msg,
        fp=io.BytesIO(b""),
    )


# ---------------------------------------------------------------------------
# get_json
# ---------------------------------------------------------------------------


class TestGetJson:
    """Tests for get_json."""

    def test_returns_parsed_json(self):
        """Successful response returns parsed JSON body."""
        payload = [{"tag_name": "1.0"}]
        mock_resp = _make_response(json.dumps(payload).encode())

        with patch("aggregation.github_api._open_request", return_value=mock_resp):
            result = get_json("https://api.github.com/repos/x/y/releases")

        assert result == payload

    def test_no_auth_header_without_token(self, monkeypatch):
        """No Authorization header is set when GITHUB_TOKEN is absent."""
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)

        captured_req = {}

        def fake_urlopen(req):
            captured_req["req"] = req
            return _make_response(b"[]")

        with patch("aggregation.github_api._open_request", side_effect=fake_urlopen):
            get_json("https://api.github.com/test")

        assert "Authorization" not in captured_req["req"].headers

    def test_no_auth_header_with_empty_token(self, monkeypatch):
        """No Authorization header is added when GITHUB_TOKEN is empty / whitespace."""
        monkeypatch.setenv("GITHUB_TOKEN", "   ")

        captured_req = {}

        def fake_urlopen(req):
            captured_req["req"] = req
            return _make_response(b"[]")

        with patch("aggregation.github_api._open_request", side_effect=fake_urlopen):
            get_json("https://api.github.com/test")

        assert "Authorization" not in captured_req["req"].headers

    def test_auth_header_present_with_token(self, monkeypatch):
        """Authorization header is set when GITHUB_TOKEN is non-empty."""
        monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken")

        captured_req = {}

        def fake_urlopen(req):
            captured_req["req"] = req
            return _make_response(b"[]")

        with patch("aggregation.github_api._open_request", side_effect=fake_urlopen):
            get_json("https://api.github.com/test")

        assert captured_req["req"].get_header("Authorization") == "Bearer ghp_testtoken"

    def test_raises_on_http_error(self):
        """HTTPError is wrapped in GitHubAPIError."""
        with patch(
            "aggregation.github_api._open_request", side_effect=_make_http_error(404)
        ):
            with pytest.raises(GitHubAPIError, match="HTTP 404"):
                get_json("https://api.github.com/test")

    def test_raises_on_rate_limit_403(self):
        """403 with zero remaining rate-limit mentions GITHUB_TOKEN in the error."""
        err = _make_http_error(
            403,
            {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1700000000"},
        )
        with patch("aggregation.github_api._open_request", side_effect=err):
            with pytest.raises(GitHubAPIError, match="GITHUB_TOKEN"):
                get_json("https://api.github.com/test")

    def test_raises_on_url_error(self):
        """URLError (network failure) is wrapped in GitHubAPIError."""
        net_err = urllib.error.URLError(reason="Name or service not known")
        with patch("aggregation.github_api._open_request", side_effect=net_err):
            with pytest.raises(GitHubAPIError, match="network error"):
                get_json("https://api.github.com/test")

    def test_raises_on_invalid_json(self):
        """Invalid JSON body raises GitHubAPIError."""
        with patch(
            "aggregation.github_api._open_request",
            return_value=_make_response(b"not-json"),
        ):
            with pytest.raises(GitHubAPIError, match="invalid JSON"):
                get_json("https://api.github.com/test")

    def test_raises_on_timeout(self):
        with patch(
            "aggregation.github_api._open_request", side_effect=TimeoutError("timeout")
        ):
            with pytest.raises(GitHubAPIError, match="network error"):
                get_json("https://api.github.com/test")


# ---------------------------------------------------------------------------
# list_repo_releases
# ---------------------------------------------------------------------------


class TestListRepoReleases:
    """Tests for list_repo_releases."""

    def test_single_page(self):
        """Single page of releases — returns the page contents."""
        page1 = [{"tag_name": "1.0"}, {"tag_name": "2.0"}]

        responses = [
            _make_response(json.dumps(page1).encode()),
            _make_response(json.dumps([]).encode()),
        ]

        with patch("aggregation.github_api._open_request", side_effect=responses):
            result = list_repo_releases("owner", "repo")

        assert result == page1

    def test_multiple_pages_concatenated(self):
        """Multiple pages are concatenated into one list."""
        page1 = [{"tag_name": f"{i}.0"} for i in range(100)]
        page2 = [{"tag_name": f"{i}.0"} for i in range(100, 150)]

        responses = [
            _make_response(json.dumps(page1).encode()),
            _make_response(json.dumps(page2).encode()),
            _make_response(json.dumps([]).encode()),
        ]

        with patch("aggregation.github_api._open_request", side_effect=responses):
            result = list_repo_releases("owner", "repo")

        assert len(result) == 150
        assert result == page1 + page2

    def test_stops_on_empty_page(self):
        """Pagination loop terminates on an empty page, not on IndexError."""
        page1 = [{"tag_name": "1.0"}]

        responses = [
            _make_response(json.dumps(page1).encode()),
            _make_response(b"[]"),
        ]

        with patch("aggregation.github_api._open_request", side_effect=responses):
            result = list_repo_releases("owner", "repo")

        assert len(result) == 1

    def test_raises_on_empty_first_page(self):
        """Empty first page (repo has no releases) raises GitHubAPIError."""
        with patch(
            "aggregation.github_api._open_request", return_value=_make_response(b"[]")
        ):
            with pytest.raises(GitHubAPIError, match="zero releases"):
                list_repo_releases("owner", "repo")

    def test_raises_on_fetch_failure(self):
        """GitHubAPIError from get_json propagates without swallowing."""
        with patch(
            "aggregation.github_api._open_request",
            side_effect=_make_http_error(500),
        ):
            with pytest.raises(GitHubAPIError):
                list_repo_releases("owner", "repo")

    def test_raises_on_non_list_response(self):
        """Non-list JSON (e.g. error dict) raises GitHubAPIError."""
        error_body = json.dumps({"message": "Not Found"}).encode()
        with patch(
            "aggregation.github_api._open_request",
            return_value=_make_response(error_body),
        ):
            with pytest.raises(GitHubAPIError, match="unexpected type"):
                list_repo_releases("owner", "repo")
