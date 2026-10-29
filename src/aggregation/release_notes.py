"""Format release notes from pre-fetched GitHub release data."""

import re
import sys
from datetime import datetime
from pathlib import Path

from .transformer import cleanup_github_markdown

GITHUB_RELEASES_URL = "https://github.com/gardenlinux/gardenlinux/releases/tag"
GITHUB_COMMITS_URL = "https://github.com/gardenlinux/gardenlinux/commit"

# Configuration
ARCHIVED_DIR = "archived"


def parse_version(tag: str) -> tuple:
    """Parse version string into comparable tuple for semantic versioning.

    Examples:
        2150.1.0 -> (2150, 1, 0)
        1877 -> (1877, 0, 0)
        1592.18.0 -> (1592, 18, 0)
    """
    # Remove leading 'v' if present
    tag = tag.lstrip("v")

    # Split by dots and convert to integers
    parts = tag.split(".")
    version_nums = []
    for part in parts:
        # Extract numeric part (handle cases like 2150.1.0, 576.3.0)
        match = re.match(r"(\d+)", part)
        if match:
            version_nums.append(int(match.group(1)))
        else:
            version_nums.append(0)

    # Pad with zeros for versions with fewer parts
    while len(version_nums) < 3:
        version_nums.append(0)

    return tuple(version_nums[:3])  # Take first 3 parts


def sort_by_version(releases: list) -> list:
    """Sort releases by semantic version (highest first)."""
    return sorted(
        releases, key=lambda r: parse_version(r.get("tag_name", "0")), reverse=True
    )


def format_release_date(date_str: str) -> str:
    """Format ISO date to readable format."""
    if not date_str:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return date_str


def format_release_entry(release: dict) -> str:
    """Format a single release as markdown with full content."""
    tag_name = release.get("tag_name", "Unknown")
    name = release.get("name") or tag_name
    body = release.get("body", "*No release notes provided*")
    published_at = release.get("published_at", "")
    html_url = release.get("html_url", f"{GITHUB_RELEASES_URL}/{tag_name}")
    prerelease = release.get("prerelease", False)

    # Extract commit hash and create GitHub link
    target = release.get("target_commitish", "")
    commit_short = target[:8] if target else ""
    commit_url = f"{GITHUB_COMMITS_URL}/{target}" if target else ""

    date_str = format_release_date(published_at)

    # Clean up GitHub markdown for VitePress compatibility
    body = cleanup_github_markdown(body)

    # Header with Published, Commit, and GitHub Release
    header = f"## {name}\n"
    if prerelease:
        header += "*Pre-release*\n\n"
    header += f"**Published:** {date_str}\n\n"
    header += f"**Commit:** [{commit_short}]({commit_url})\n\n"
    header += f"**GitHub Release:** [{tag_name}]({html_url})\n\n"

    return f"{header}{body.strip()}\n"


def render_release_page(
    tag_name: str,
    date: str,
    release_order: int,
    content: str,
) -> str:
    """Render the full markdown page for a single release note."""
    return f"""---
title: "Release {tag_name}"
description: "Release notes for Garden Linux {tag_name}, published at {date}."
order: {release_order}
editLink: false
related_topics:
  - /reference/releases/release-lifecycle
  - /reference/releases/maintained-releases
  - /reference/releases/archived-releases
  - /reference/releases/release-notes/
---

{content}

## Related Topics

<RelatedTopics />

"""


def render_redirect_page(
    tag_name: str,
    date: str,
    release_order: int,
    target: str,
) -> str:
    """Render a contentless top-level alias page that forwards to ``target``.

    Archived releases keep a stable URL at the top-level release-notes path.
    The alias is a real VitePress route (so in-site links resolve instead of
    hitting a client-side 404, and the archived sidebar entry is selected) but
    carries no release content.  A client-side redirect covers in-site (SPA)
    navigation, while the ``head`` meta refresh covers loads without
    JavaScript.  ``target`` is relative to the alias page, so it works
    regardless of the configured ``base`` path.
    """
    return f"""---
title: "Release {tag_name}"
description: "Release notes for Garden Linux {tag_name}, published at {date}."
order: {release_order}
editLink: false
exclude: true
head:
  - - meta
    - http-equiv: refresh
      content: "0; url={target}"
---

<script setup>
import {{ onMounted }} from 'vue'
import {{ useData }} from 'vitepress'

const {{ site }} = useData()

onMounted(() => {{
  window.location.replace(
    site.value.base + 'reference/releases/release-notes/{target}'
  )
}})
</script>

# Release {tag_name}

The release notes have moved to the [archived release notes]({target}).
"""


def generate_release_notes_docs(
    docs_dir: Path,
    releases: list[dict],
    active_versions: set[str],
) -> bool:
    """Generate release-notes documentation files from a pre-fetched release list.

    The caller (``aggregate.py``) is responsible for fetching the full release
    list via :func:`aggregation.github_api.list_repo_releases` before calling
    this function.  No network requests are made here.

    Args:
        docs_dir: Root of the VitePress ``docs/`` tree.
        releases: Full list of GitHub release objects as returned by the GitHub
            Releases API (already fetched and validated by the caller).
        active_versions: Effective active minor version strings.  A release is
            routed to the maintained tree when its version is in this set and to
            the archived tree otherwise.

    Returns:
        ``True`` on success, ``False`` if no releases were provided.
    """
    releases_dir = docs_dir / "reference" / "releases" / "release-notes"
    releases_dir.mkdir(parents=True, exist_ok=True)

    archived_dir = releases_dir / ARCHIVED_DIR
    archived_dir.mkdir(parents=True, exist_ok=True)

    # Clean up existing release notes (except index.md and archived/index.md)
    for md_file in releases_dir.glob("*.md"):
        if md_file.name not in ["index.md"]:
            md_file.unlink()
            print(f"  Removed: {md_file.relative_to(docs_dir)}")

    if not releases:
        print(
            "Warning: No releases provided to generate_release_notes_docs",
            file=sys.stderr,
        )
        return False

    if not active_versions:
        print(
            "Warning: No active versions resolved, defaulting all releases to archived",
            file=sys.stderr,
        )

    # Filter releases (skip drafts)
    filtered = []
    for release in releases:
        if release.get("draft", False):
            continue
        filtered.append(release)

    # Sort by semantic version (highest first)
    filtered = sort_by_version(filtered)

    # Generate individual files for each release
    release_list = []
    for idx, release in enumerate(filtered):
        tag_name = release.get("tag_name", "Unknown")
        name = release.get("name") or tag_name

        content = format_release_entry(release)
        date = format_release_date(release.get("published_at", ""))

        # Make version heading h1 (replace ## VersionName with # VersionName)
        content = re.sub(
            r"^##\s+" + re.escape(name) + r"$", "# " + name, content, flags=re.MULTILINE
        )

        # Determine if this release is archived.
        # A release is active ONLY if it's explicitly in the active_versions set.
        # All other releases are archived.
        tag_without_v = tag_name.lstrip("v")
        is_archived = tag_without_v not in active_versions

        # Order: highest version = 1, second = 2, etc.
        release_order = idx + 1

        # Create filename from tag
        filename = tag_name.replace(".", "-") + ".md"

        # Route to appropriate directory based on archive status.
        if is_archived:
            # Archived release notes stay under archived/ (still listed there),
            # while a contentless alias at the top level forwards a stable URL
            # without `archived/` to the archived page.
            filepath = archived_dir / filename
            filepath.write_text(
                render_release_page(tag_name, date, release_order, content)
            )
            alias_path = releases_dir / filename
            alias_path.write_text(
                render_redirect_page(
                    tag_name,
                    date,
                    release_order,
                    f"{ARCHIVED_DIR}/{tag_name.replace('.', '-')}.html",
                )
            )
        else:
            filepath = releases_dir / filename
            filepath.write_text(
                render_release_page(tag_name, date, release_order, content)
            )

        release_list.append(
            {
                "tag": tag_name,
                "name": name,
                "filename": filename,
                "date": format_release_date(release.get("published_at", "")),
                "is_archived": is_archived,
            }
        )
        print(f"  Created: {filepath.relative_to(docs_dir)}")
        if is_archived:
            print(f"  Created: {alias_path.relative_to(docs_dir)}")

    print("Release notes generation complete.")
    return True
