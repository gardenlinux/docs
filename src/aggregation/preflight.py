"""Read-only checks of the credentials and repositories used by aggregation."""

import subprocess
import tempfile

from .auth import get_token, git_environment, redact_credentials, token_variable
from .github_api import GitHubAPIError, list_repo_releases
from .models import RepoConfig


def check_authentication(repos: list[RepoConfig]) -> None:
    """Require explicit credentials and verify real Git and release API access.

    ls-remote validates repository access, not availability of locked historical
    commits. The actual aggregation fetch/checkout validates those commits.
    """
    remotes = [repo for repo in repos if repo.is_remote]
    urls = [repo.url for repo in remotes] + ["https://api.github.com"]
    for url in urls:
        variable = token_variable(url)
        if variable is not None and not get_token(url):
            raise GitHubAPIError(f"Missing {variable} for {url}")

    # Do not inherit the workflow checkout's repository-local credentials.
    with tempfile.TemporaryDirectory() as cwd:
        for repo in remotes:
            try:
                subprocess.run(
                    ["git", "ls-remote", "--exit-code", repo.url, "HEAD"],
                    env=git_environment(repo.url),
                    cwd=cwd,
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
            except (subprocess.SubprocessError, OSError, ValueError) as exc:
                detail = getattr(exc, "stderr", None) or str(exc)
                raise GitHubAPIError(
                    f"Git authentication/access check failed for {repo.name}: "
                    f"{redact_credentials(detail)}"
                ) from exc
            print(f"  Git access OK: {repo.name} ({repo.url})")
    releases = list_repo_releases("gardenlinux", "gardenlinux")
    print(f"  Public releases API OK: {len(releases)} release(s)")
