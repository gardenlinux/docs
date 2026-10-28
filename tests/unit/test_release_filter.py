"""Unit tests for GLRD release-table filtering in aggregation.releases."""

import pytest

from aggregation.glrd import resolve_active_versions
from aggregation.releases import generate_release_table

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_release(
    major: int, minor: int | None = None, patch: int | None = None
) -> dict:
    """Build a minimal GLRD release dict."""
    version: dict = {"major": major}
    if minor is not None:
        version["minor"] = minor
    if patch is not None:
        version["patch"] = patch
    return {
        "version": version,
        "git": {},
        "lifecycle": {},
    }


def _make_releases_data(*releases) -> dict:
    return {"releases": list(releases)}


# ---------------------------------------------------------------------------
# Filtering: minor rows
# ---------------------------------------------------------------------------


class TestGenerateReleaseTableFiltering:
    """generate_release_table skips minor rows absent from existing_gh_tags."""

    def test_minor_row_included_when_tag_present(self):
        """A minor release present in existing_gh_tags appears in the table."""
        data = _make_releases_data(_make_release(1877, 14))
        table = generate_release_table(data, set(), existing_gh_tags={"1877.14"})
        assert "1877.14" in table

    def test_minor_row_skipped_when_tag_absent(self):
        """A minor release absent from existing_gh_tags is dropped."""
        data = _make_releases_data(_make_release(1877, 14))
        table = generate_release_table(data, set(), existing_gh_tags=set())
        assert "1877.14" not in table
        # Table should be effectively empty (header rows only)
        data_rows = [
            line
            for line in table.splitlines()
            if line.startswith("|")
            and not line.startswith("|:")
            and "Version" not in line
        ]
        assert data_rows == []

    def test_major_row_always_included(self):
        """A major-only row is emitted regardless of existing_gh_tags."""
        data = _make_releases_data(_make_release(1877))
        table = generate_release_table(data, set(), existing_gh_tags=set())
        assert "1877" in table

    def test_mixed_major_and_minor(self):
        """Major rows pass through; unmatched minor rows are dropped."""
        data = _make_releases_data(
            _make_release(2150),  # major-only — always kept
            _make_release(2150, 1, 0),  # minor — tag present
            _make_release(2150, 2, 0),  # minor — tag absent
        )
        table = generate_release_table(
            data,
            active_versions={"2150.1.0"},
            existing_gh_tags={"2150.1.0"},
        )
        assert "2150.1.0" in table
        assert "2150.2.0" not in table
        # Major row 2150 is present (as plain text, no dot-separated minor)
        assert "2150" in table

    def test_v_prefix_stripped_from_gh_tag(self):
        """Tags stored with a leading 'v' in existing_gh_tags are still matched."""
        # The caller strips 'v' before building the set, but simulate the raw
        # comparison working by stripping manually (documents the contract).
        raw_tags = {"v1877.14", "v2150.1.0"}
        normalized = {t.lstrip("v") for t in raw_tags}

        data = _make_releases_data(_make_release(1877, 14))
        table = generate_release_table(data, set(), existing_gh_tags=normalized)
        assert "1877.14" in table

    def test_patch_version_compared_correctly(self):
        """Minor+patch version strings are matched against existing_gh_tags."""
        data = _make_releases_data(_make_release(2150, 1, 0))
        table = generate_release_table(data, set(), existing_gh_tags={"2150.1.0"})
        assert "2150.1.0" in table

    def test_patch_version_absent_skipped(self):
        """Minor+patch version absent from existing_gh_tags is skipped."""
        data = _make_releases_data(_make_release(2150, 1, 0))
        table = generate_release_table(data, set(), existing_gh_tags={"2150.1"})
        # "2150.1.0" != "2150.1" — strict equality after normalization
        assert "2150.1.0" not in table

    def test_warning_written_to_stderr_for_skipped(self, capsys):
        """A warning line is written to stderr for each skipped minor release."""
        data = _make_releases_data(_make_release(1877, 99))
        generate_release_table(data, set(), existing_gh_tags=set())
        captured = capsys.readouterr()
        assert "1877.99" in captured.err
        assert "Warning" in captured.err

    def test_no_warning_for_included_minor(self, capsys):
        """No warning is written when the minor release tag is present."""
        data = _make_releases_data(_make_release(1877, 14))
        generate_release_table(data, set(), existing_gh_tags={"1877.14"})
        captured = capsys.readouterr()
        assert "1877.14" not in captured.err

    def test_empty_releases_data(self):
        """Empty releases dict returns the 'no releases' sentinel."""
        table = generate_release_table({}, set(), existing_gh_tags=set())
        assert "*No releases found*" in table

    def test_empty_releases_list(self):
        """Empty releases list returns the 'no releases' sentinel."""
        table = generate_release_table({"releases": []}, set(), existing_gh_tags=set())
        assert "*No releases found*" in table

    def test_glrd_release_exists_but_no_github_release(self):
        """GLRD lists a minor release that has no corresponding GitHub release tag.

        This is the primary guard this filtering was designed for: a GLRD entry
        whose tag was never pushed to GitHub (e.g. a planned but unpublished
        release).  The row must be dropped from the generated table and a
        warning must appear on stderr.
        """
        # GitHub has released 2150.0.0 and 2150.1.0 but NOT 2150.2.0.
        # GLRD, however, already lists 2150.2.0 (e.g. an upcoming release).
        existing_gh_tags = {"2150.0.0", "2150.1.0"}
        data = _make_releases_data(
            _make_release(2150, 0, 0),
            _make_release(2150, 1, 0),
            _make_release(2150, 2, 0),  # in GLRD, but NO matching GitHub release
        )
        table = generate_release_table(
            data,
            active_versions={"2150.1.0"},
            existing_gh_tags=existing_gh_tags,
        )

        # Releases that DO have GitHub tags are included.
        assert "2150.0.0" in table
        assert "2150.1.0" in table
        # The GLRD-only entry is absent.
        assert "2150.2.0" not in table

    def test_glrd_release_exists_but_no_github_release_emits_warning(self, capsys):
        """A warning naming the missing version is written to stderr."""
        existing_gh_tags = {"2150.0.0"}
        data = _make_releases_data(
            _make_release(2150, 0, 0),
            _make_release(2150, 1, 0),  # GLRD only — no GitHub tag
        )
        generate_release_table(
            data,
            active_versions=set(),
            existing_gh_tags=existing_gh_tags,
        )
        captured = capsys.readouterr()
        assert "2150.1.0" in captured.err
        assert "Warning" in captured.err
        # The present release must NOT trigger a warning.
        assert "2150.0.0" not in captured.err


class TestResolveActiveVersions:
    """resolve_active_versions falls back when GLRD is ahead of GitHub."""

    def test_active_version_backed_by_gh_release_is_kept(self):
        """An active version that also exists on GitHub is kept unchanged."""
        data = _make_releases_data(_make_release(2150, 13, 0))
        resolved = resolve_active_versions(
            {"2150.13.0"}, existing_gh_tags={"2150.13.0"}, releases_data=data
        )
        assert resolved == {"2150.13.0"}

    def test_falls_back_to_newest_older_gh_release(self):
        """A GLRD-only active version falls back to the newest GH-backed minor.

        Reproduces the production case: GLRD lists 2150.14.0 as active but the
        newest GitHub release is 2150.13.0.
        """
        data = _make_releases_data(
            _make_release(2150, 12, 0),
            _make_release(2150, 13, 0),
            _make_release(2150, 14, 0),  # in GLRD, but NOT on GitHub
        )
        resolved = resolve_active_versions(
            {"2150.14.0"},
            existing_gh_tags={"2150.12.0", "2150.13.0"},
            releases_data=data,
        )
        assert resolved == {"2150.13.0"}

    def test_fallback_does_not_cross_major(self):
        """Fallback candidates are restricted to the same major version."""
        data = _make_releases_data(
            _make_release(1877, 26),
            _make_release(2150, 14, 0),
        )
        resolved = resolve_active_versions(
            {"2150.14.0"},
            existing_gh_tags={"1877.26"},
            releases_data=data,
        )
        assert resolved == set()

    def test_no_fallback_available_drops_version_and_warns(self, capsys):
        """When no older GH-backed release exists the version is dropped."""
        data = _make_releases_data(_make_release(2150, 14, 0))
        resolved = resolve_active_versions(
            {"2150.14.0"}, existing_gh_tags=set(), releases_data=data
        )
        assert resolved == set()
        captured = capsys.readouterr()
        assert "2150.14.0" in captured.err
        assert "Warning" in captured.err

    def test_multiple_active_versions_resolved_independently(self):
        """Each active version is resolved against its own major's candidates."""
        data = _make_releases_data(
            _make_release(1877, 26),
            _make_release(2150, 13, 0),
            _make_release(2150, 14, 0),
        )
        resolved = resolve_active_versions(
            {"1877.26", "2150.14.0"},
            existing_gh_tags={"1877.26", "2150.13.0"},
            releases_data=data,
        )
        assert resolved == {"1877.26", "2150.13.0"}

    def test_missing_releases_data_drops_all(self, capsys):
        """A None releases_data leads to no fallbacks (and warnings)."""
        resolved = resolve_active_versions(
            {"2150.14.0"}, existing_gh_tags=set(), releases_data=None
        )
        assert resolved == set()
        assert "Warning" in capsys.readouterr().err
