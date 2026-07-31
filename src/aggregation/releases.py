"""Generate release documentation from GLRD.

The :func:`generate_release_docs` and :func:`generate_release_table` functions
accept a pre-built ``existing_gh_tags`` set that was fetched from the GitHub
Releases API by the caller (``aggregate.py``).  GLRD rows that carry a
``minor`` version component are skipped when their normalized version string
(``{major}.{minor}[.{patch}]``) is absent from that set.  Major-only rows are
always emitted.  One warning line per skipped row is written to ``stderr`` so
that CI logs surface the omission.
"""

import sys
from pathlib import Path

from .constants import COMMITS_URL, GANTT_THEME, LIFECYCLE_LINKS
from .glrd import get_active_minor_versions, run_glrd_json


def format_version(release: dict, active_versions: set[str]) -> tuple[str, str]:
    """Extract version string and link from release data.

    Args:
        release: Release data from GLRD
        active_versions: Set of active minor version strings

    Returns:
        Tuple of (version_string, version_link)
        - Active minor releases: link to release-notes/{version}.html
        - Archived minor releases: link to release-notes/archived/{version}.html
        - Major releases: no link (just plain text)
    """
    version_obj = release.get("version", {})

    has_minor = "minor" in version_obj

    if "major" in version_obj and "minor" in version_obj:
        if "patch" in version_obj:
            version_str = (
                f"{version_obj['major']}.{version_obj['minor']}.{version_obj['patch']}"
            )
        else:
            version_str = f"{version_obj['major']}.{version_obj['minor']}"
    elif "major" in version_obj:
        version_str = str(version_obj["major"])
    else:
        return "N/A", "N/A"

    # Only link minor releases to release notes; major releases have no link
    if has_minor:
        # Check if this version is active
        is_active = version_str in active_versions

        if is_active:
            version_link = (
                f"[{version_str}](release-notes/{version_str.replace('.', '-')}.html)"
            )
        else:
            version_link = f"[{version_str}](release-notes/archived/{version_str.replace('.', '-')}.html)"
    else:
        version_link = version_str  # Major release - no link

    return version_str, version_link


def format_commit(release: dict) -> str:
    """Extract commit info and create GitHub link from release data."""
    git_info = release.get("git", {})
    commit_short = git_info.get("commit_short", "")
    commit_full = git_info.get("commit", "")

    if commit_short and commit_full:
        return f"[`{commit_short}`]({COMMITS_URL}/{commit_full})"
    elif commit_short:
        return f"`{commit_short}`"
    return "—"


def format_lifecycle_date(lifecycle: dict, key: str) -> str:
    """Extract and format lifecycle date with link."""
    date_obj = lifecycle.get(key, {})
    isodate = date_obj.get("isodate", "")

    if not isodate:
        return "—"

    # Map keys to LIFECYCLE_LINKS
    link_key = key
    if key == "released":
        link_key = "standard"  # released = start of standard maintenance

    anchor = LIFECYCLE_LINKS.get(link_key, "")
    return f"[{isodate}]({anchor})" if anchor else isodate


def generate_mermaid_gantt(releases_data: dict) -> str:
    """Generate Mermaid Gantt chart from GLRD JSON data."""
    if not releases_data or "releases" not in releases_data:
        return ""

    releases = releases_data.get("releases", [])
    major_releases = [r for r in releases if r.get("type") == "major"]

    if not major_releases:
        return ""

    gantt = GANTT_THEME + """
gantt
    title Garden Linux Release Maintenance Phases
    dateFormat YYYY-MM-DD
    axisFormat %m/%y
"""
    for release in major_releases:
        version = release.get("version", {}).get("major")
        if not version:
            continue

        lifecycle = release.get("lifecycle", {})
        released = lifecycle.get("released", {})
        extended = lifecycle.get("extended", {})
        eol = lifecycle.get("eol", {})

        if not released or not eol:
            continue

        released_date = released.get("isodate", "")
        extended_date = extended.get("isodate", "") if extended else ""
        eol_date = eol.get("isodate", "")

        if not released_date or not eol_date:
            continue

        gantt += f"    section {version}\n"

        if extended_date:
            gantt += f"    Standard Maintenance           :active, sm{version}, {released_date}, {extended_date}\n"
            gantt += f"    Extended Maintenance         :crit, em{version}, {extended_date}, {eol_date}\n"
        else:
            gantt += f"    Standard Maintenance           :active, sm{version}, {released_date}, {eol_date}\n"

        gantt += f"    EOM          :milestone, eom{version}, {eol_date}, 0d\n"

    return gantt


def generate_release_table(
    releases_data: dict,
    active_versions: set[str],
    existing_gh_tags: set[str],
) -> str:
    """Generate markdown table from GLRD JSON data.

    GLRD rows that carry a ``minor`` version component are only included when
    their normalized version string (``{major}.{minor}[.{patch}]``) appears in
    *existing_gh_tags*.  Rows without a matching GitHub release tag are skipped
    and a warning is written to ``stderr``.  Major-only rows are always emitted
    regardless of *existing_gh_tags*.

    Args:
        releases_data: Release data from GLRD.
        active_versions: Set of active minor version strings (used for link
            routing, not for inclusion filtering).
        existing_gh_tags: Set of GitHub release tag names with leading ``v``
            stripped (e.g. ``{"1877.14", "2150.1.0"}``).  Built from the full
            list fetched by :func:`aggregation.github_api.list_repo_releases`.
    """
    if not releases_data or "releases" not in releases_data:
        return "*No releases found*"

    releases = releases_data.get("releases", [])
    if not releases:
        return "*No releases found*"

    table = "| Version | Commit | Standard Maintenance | Extended Maintenance | End of Maintenance |\n"
    table += "|:--------|:-------|:---------------------|:---------------------|:-------------------|\n"

    for release in releases:
        version_obj = release.get("version", {})
        has_minor = "minor" in version_obj

        if has_minor:
            # Build the normalized version string for tag comparison.
            if "patch" in version_obj:
                version_str = f"{version_obj['major']}.{version_obj['minor']}.{version_obj['patch']}"
            else:
                version_str = f"{version_obj['major']}.{version_obj['minor']}"

            if version_str not in existing_gh_tags:
                print(
                    f"Warning: skipping GLRD version {version_str} — no GitHub release found",
                    file=sys.stderr,
                )
                continue

        _, version_link = format_version(release, active_versions)
        commit_link = format_commit(release)

        lifecycle = release.get("lifecycle", {})
        standard_maint = format_lifecycle_date(lifecycle, "released")
        extended_maint = format_lifecycle_date(lifecycle, "extended")
        eol_date = format_lifecycle_date(lifecycle, "eol")

        table += f"| {version_link} | {commit_link} | {standard_maint} | {extended_maint} | {eol_date} |\n"

    return table


def get_timeline_section(gantt_chart: str, title: str) -> str:
    """Build timeline section with Gantt chart and legend."""
    if not gantt_chart:
        return ""

    return f"""

## {title}

```mermaid
{gantt_chart}
```

**Legend:**
- [Standard Maintenance]({LIFECYCLE_LINKS['standard']}) — Active maintenance with regular updates
- [Extended Maintenance]({LIFECYCLE_LINKS['extended']}) — Critical CVE fixes only (CVSS ≥7.0)
- **EOM** = [End of Maintenance]({LIFECYCLE_LINKS['eol']}) — No further updates
"""


def append_release_page(
    table: str, timeline: str, page_type: str = "maintained"
) -> str:
    """Append to an existing release page."""

    return f"""
{table}{timeline}

## Related Topics

<RelatedTopics />

"""


def generate_release_docs(docs_dir: Path, existing_gh_tags: set[str]) -> bool:
    """Fetch release data from GLRD and generate release documentation pages.

    GLRD minor releases are only included in the generated tables when a
    matching GitHub release tag exists in *existing_gh_tags* (see
    :func:`generate_release_table`).

    Args:
        docs_dir: Root of the VitePress ``docs/`` tree.
        existing_gh_tags: Set of GitHub release tag names with leading ``v``
            stripped.  Built from the full list fetched by the caller
            (``aggregate.py``) via
            :func:`aggregation.github_api.list_repo_releases`.
    """
    releases_dir = docs_dir / "reference" / "releases"
    releases_dir.mkdir(parents=True, exist_ok=True)

    print("Generating release documentation from GLRD...")

    # Get active minor versions for correct link generation
    active_versions = get_active_minor_versions()
    print(f"  Found {len(active_versions)} active minor versions")

    active_data = run_glrd_json(["--active"])
    archived_data = run_glrd_json(["--archived"])

    if active_data is None:
        print(
            "Warning: Could not fetch active releases - skipping generation",
            file=sys.stderr,
        )
        return False

    active_table = generate_release_table(
        active_data, active_versions, existing_gh_tags
    )
    active_gantt = generate_mermaid_gantt(active_data)
    active_timeline = get_timeline_section(active_gantt, "Release Timeline")

    active_content = append_release_page(
        active_table,
        active_timeline,
        "maintained",
    )

    release_file = "maintained-releases.md"
    release_path = releases_dir / release_file

    # The static page (frontmatter, intro, headings) is aggregated from the
    # gardenlinux repo via 'github_target_path'. If it was not aggregated (for
    # example because the source 'docs/' tree is absent at the pinned commit),
    # skip generation with a warning rather than crashing the whole build.
    if not release_path.exists():
        print(
            f"Warning: {release_path} not found — skipping maintained-releases "
            "generation. Ensure the source page is aggregated from the "
            "gardenlinux repo (github_target_path frontmatter).",
            file=sys.stderr,
        )
        return False

    # Read existing file and keep only frontmatter and static content
    # (everything before the generated tables)
    existing_content = release_path.read_text()
    lines = existing_content.split("\n")

    # Find where the generated content starts (look for "## Active Releases" heading)
    static_lines = []
    for i, line in enumerate(lines):
        if line.startswith("## Active Releases") or line.startswith(
            "## Release Timeline"
        ):
            break
        static_lines.append(line)

    # Write static content plus new generated content
    release_path.write_text("\n".join(static_lines).rstrip() + "\n\n" + active_content)
    print(f"  Updated: {release_path}")

    if archived_data is not None:
        archived_table = generate_release_table(
            archived_data, active_versions, existing_gh_tags
        )
        archived_gantt = generate_mermaid_gantt(archived_data)
        archived_timeline = get_timeline_section(
            archived_gantt, "Archived Releases Timeline"
        )

        archived_content = append_release_page(
            archived_table,
            archived_timeline,
            "archived",
        )

        release_file = "archived-releases.md"
        release_path = releases_dir / release_file

        # As with maintained-releases, the static page is aggregated from the
        # gardenlinux repo. Skip gracefully if it was not aggregated.
        if not release_path.exists():
            print(
                f"Warning: {release_path} not found — skipping archived-releases "
                "generation. Ensure the source page is aggregated from the "
                "gardenlinux repo (github_target_path frontmatter).",
                file=sys.stderr,
            )
            print("Release documentation generation complete.")
            return True

        # Read existing file and keep only frontmatter and static content
        existing_content = release_path.read_text()
        lines = existing_content.split("\n")

        # Find where the generated content starts (look for "## Out of Maintenance" heading)
        static_lines = []
        for i, line in enumerate(lines):
            if line.startswith("## Out of Maintenance") or line.startswith(
                "## Archived Releases Timeline"
            ):
                break
            static_lines.append(line)

        # Write static content plus new generated content
        release_path.write_text(
            "\n".join(static_lines).rstrip() + "\n\n" + archived_content
        )
        print(f"  Updated: {release_path}")
    else:
        print("Warning: Could not fetch archived releases", file=sys.stderr)

    print("Release documentation generation complete.")
    return True
