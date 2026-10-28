"""Generate release documentation from GLRD."""

import json
import re
import subprocess
import sys


def run_glrd_json(args: list[str]) -> dict | None:
    """Run glrd command with JSON output and return parsed data."""
    try:
        result = subprocess.run(
            ["glrd"] + args + ["--output-format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        print(f"glrd command failed: {result.stderr}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("glrd not found - install with: pip install glrd", file=sys.stderr)
        return None
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error running glrd: {e}", file=sys.stderr)
        return None


def get_active_minor_versions() -> set[str]:
    """Get set of active minor release versions from GLRD.

    Returns:
        Set of version strings (e.g., {"1877.14", "2150.1.0"})
    """
    active_versions = set()

    try:
        result = subprocess.run(
            ["glrd", "--active", "--type", "minor", "--output-format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            releases = data.get("releases", [])
            for release in releases:
                version_obj = release.get("version", {})
                if "major" in version_obj and "minor" in version_obj:
                    if "patch" in version_obj:
                        version = f"{version_obj['major']}.{version_obj['minor']}.{version_obj['patch']}"
                    else:
                        version = f"{version_obj['major']}.{version_obj['minor']}"
                    active_versions.add(version)
    except (json.JSONDecodeError, Exception) as e:
        print(f"Warning: Failed to query active minor versions: {e}", file=sys.stderr)

    return active_versions


def _parse_version(version_str: str) -> tuple[int, int, int]:
    """Parse a version string into a comparable ``(major, minor, patch)`` tuple."""
    parts = [int(part) for part in re.findall(r"\d+", version_str)]
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def resolve_active_versions(
    glrd_active_versions: set[str],
    existing_gh_tags: set[str],
    releases_data: dict | None,
) -> set[str]:
    """Resolve the effective set of active minor versions.

    GLRD marks the newest minor release of each major as active, but a matching
    GitHub Release may not exist yet (for example an upcoming release that has
    been published to GLRD but not to GitHub).  For every active minor without a
    GitHub release, fall back to the newest GLRD minor of the same major that
    *does* have one.

    Args:
        glrd_active_versions: Active minor versions as reported by GLRD (e.g.
            ``{"1877.26", "2150.14.0"}``).
        existing_gh_tags: GitHub release tags with the leading ``v`` stripped
            (e.g. ``{"2150.13.0", "1877.26"}``).
        releases_data: Full GLRD release data (all releases), used to discover
            candidate fallback versions.

    Returns:
        Set of version strings that are active per GLRD and backed by a GitHub
        release (e.g. ``{"1877.26", "2150.13.0"}``).
    """
    # Group every GLRD minor that has a GitHub release by its major version.
    candidates: dict[int, set[str]] = {}
    for release in (releases_data or {}).get("releases", []):
        version_obj = release.get("version", {})
        if "major" not in version_obj or "minor" not in version_obj:
            continue
        if "patch" in version_obj:
            version_str = (
                f"{version_obj['major']}.{version_obj['minor']}.{version_obj['patch']}"
            )
        else:
            version_str = f"{version_obj['major']}.{version_obj['minor']}"
        if version_str in existing_gh_tags:
            candidates.setdefault(version_obj["major"], set()).add(version_str)

    resolved: set[str] = set()
    for active in glrd_active_versions:
        if active in existing_gh_tags:
            resolved.add(active)
            continue

        major = int(active.split(".")[0])
        options = candidates.get(major, set())
        if options:
            fallback = max(options, key=_parse_version)
            print(
                f"  Active GLRD version {active} has no GitHub release — "
                f"falling back to {fallback}",
            )
            resolved.add(fallback)
        else:
            print(
                f"Warning: active GLRD version {active} has no GitHub release "
                "and no older release is available — skipping",
                file=sys.stderr,
            )

    return resolved
