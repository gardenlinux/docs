"""Host-specific credentials shared by Git fetching and GitHub API calls.

Explicit tokens are supplied through subprocess environment configuration only;
they are never written to URLs, command arguments, or Git configuration files.
"""

import base64
import os
from urllib.parse import urlsplit

TOKEN_VARIABLES = {
    "github.com": "GH_COM_TOKEN",
    "api.github.com": "GH_COM_TOKEN",
}
TOKEN_ENV_NAMES = ("GH_COM_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_TOKEN")


def token_variable(url: str) -> str | None:
    """Return the credential variable for an exact, trusted HTTPS host."""
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.port not in (None, 443)
    ):
        return None
    if parsed.hostname in TOKEN_VARIABLES:
        return TOKEN_VARIABLES[parsed.hostname]
    enterprise_host = os.environ.get("GH_ENTERPRISE_HOST", "").strip().lower()
    if enterprise_host:
        enterprise = urlsplit(f"https://{enterprise_host}")
        if (
            enterprise.hostname != enterprise_host
            or enterprise.path
            or enterprise.query
            or enterprise.fragment
        ):
            raise ValueError("GH_ENTERPRISE_HOST must be a hostname, not a URL")
        if parsed.hostname == enterprise_host:
            return "GH_ENTERPRISE_TOKEN"
    return None


def get_token(url: str) -> str:
    """Select a token; GITHUB_TOKEN is a public-host-only compatibility alias."""
    variable = token_variable(url)
    if variable is None:
        return ""
    token = os.environ.get(variable, "").strip()
    if not token and variable == "GH_COM_TOKEN":
        token = os.environ.get("GITHUB_TOKEN", "").strip()
    if "\n" in token or "\r" in token:
        raise ValueError(f"{variable} must not contain line breaks")
    return token


def validate_remote_url(url: str) -> None:
    """Reject embedded credentials before a repository URL can be logged."""
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Remote repositories require an HTTPS URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError(
            "Repository URLs must not contain credentials; use token variables"
        )


def git_environment(url: str) -> dict[str, str]:
    """Build isolated, non-persistent Git authentication for one repository."""
    validate_remote_url(url)
    token = get_token(url)
    env = os.environ.copy()
    for variable in TOKEN_ENV_NAMES:
        env.pop(variable, None)
    if env.get("CI", "").lower() in ("true", "1") or token:
        env["GIT_TERMINAL_PROMPT"] = "0"
        env["GCM_INTERACTIVE"] = "Never"
    if not token:
        # Keep the user's credential manager available for local development.
        return env

    # Disable trace output, which can include the encoded Authorization header.
    for key in list(env):
        if key.startswith("GIT_TRACE") or key == "GIT_CURL_VERBOSE":
            env.pop(key)
    scope = url.rstrip("/")
    basic = base64.b64encode(f"x-access-token:{token}".encode()).decode()
    settings = [
        ("credential.helper", ""),
        (f"http.{scope}.extraHeader", ""),
        (f"http.{scope}.extraHeader", f"Authorization: Basic {basic}"),
        (f"http.{scope}.followRedirects", "false"),
    ]
    count = int(env.get("GIT_CONFIG_COUNT", "0"))
    for key, value in settings:
        env[f"GIT_CONFIG_KEY_{count}"] = key
        env[f"GIT_CONFIG_VALUE_{count}"] = value
        count += 1
    env["GIT_CONFIG_COUNT"] = str(count)
    return env


def redact_credentials(message: str) -> str:
    """Remove raw and Git-encoded tokens from subprocess error output."""
    for variable in TOKEN_ENV_NAMES:
        token = os.environ.get(variable, "").strip()
        if token:
            encoded = base64.b64encode(f"x-access-token:{token}".encode()).decode()
            message = message.replace(encoded, "[REDACTED]").replace(
                token, "[REDACTED]"
            )
    return message
