"""Unit tests for aggregation.release_notes page generation."""

from pathlib import Path

from aggregation.release_notes import (
    generate_release_notes_docs,
    render_redirect_page,
    render_release_page,
)


def _make_release(tag: str, name: str | None = None, draft: bool = False) -> dict:
    """Build a minimal GitHub release dict."""
    return {
        "tag_name": tag,
        "name": name or tag,
        "body": "Some release body.",
        "published_at": "2026-10-26T00:00:00Z",
        "html_url": f"https://github.com/gardenlinux/gardenlinux/releases/tag/{tag}",
        "prerelease": False,
        "target_commitish": "92024ecb52a80dd0646705b8de828f09c1d81a64",
        "draft": draft,
    }


class TestRenderReleasePage:
    """render_release_page controls the generated frontmatter."""

    def test_has_expected_frontmatter(self):
        page = render_release_page("1877.26", "October 13, 2026", 1, "# body")
        assert page.startswith("---\n")
        assert 'title: "Release 1877.26"' in page
        assert "order: 1" in page
        assert "related_topics:" in page
        assert "exclude" not in page


class TestRenderRedirectPage:
    """render_redirect_page builds a contentless forwarding alias."""

    def test_excluded_with_meta_refresh_and_client_redirect(self):
        page = render_redirect_page(
            "2150.13.0", "October 26, 2026", 2, "archived/2150-13-0.html"
        )
        assert page.startswith("---\n")
        assert 'title: "Release 2150.13.0"' in page
        assert "exclude: true" in page
        # meta refresh fallback (no JavaScript) with a relative target
        assert 'content: "0; url=archived/2150-13-0.html"' in page
        # client-side redirect for in-site (SPA) navigation
        assert "window.location.replace" in page
        assert "archived/2150-13-0.html" in page
        # The alias must not carry the release body.
        assert "related_topics" not in page


class TestGenerateReleaseNotesDocs:
    """generate_release_notes_docs routes pages and writes top-level aliases."""

    def _run(self, tmp_path: Path, releases, active_versions):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        assert generate_release_notes_docs(docs_dir, releases, active_versions)
        releases_dir = docs_dir / "reference" / "releases" / "release-notes"
        return docs_dir, releases_dir

    def test_active_release_is_top_level_without_alias(self, tmp_path):
        _, releases_dir = self._run(tmp_path, [_make_release("1877.26")], {"1877.26"})

        page = releases_dir / "1877-26.md"
        assert page.exists()
        assert not (releases_dir / "archived" / "1877-26.md").exists()
        assert "exclude" not in page.read_text()

    def test_archived_release_writes_page_and_top_level_alias(self, tmp_path):
        _, releases_dir = self._run(tmp_path, [_make_release("2150.13.0")], set())

        assert (releases_dir / "archived" / "2150-13-0.md").exists()

        alias = releases_dir / "2150-13-0.md"
        assert alias.exists()
        alias_content = alias.read_text()
        assert "exclude: true" in alias_content
        assert "url=archived/2150-13-0.html" in alias_content

    def test_alias_is_contentless(self, tmp_path):
        _, releases_dir = self._run(tmp_path, [_make_release("2150.13.0")], set())

        alias_content = (releases_dir / "2150-13-0.md").read_text()
        archived_content = (releases_dir / "archived" / "2150-13-0.md").read_text()

        assert "# 2150.13.0" not in alias_content
        assert "Some release body." not in alias_content
        assert "# 2150.13.0" in archived_content

    def test_no_public_stub_is_written(self, tmp_path):
        docs_dir, _ = self._run(tmp_path, [_make_release("2150.13.0")], set())
        assert not (docs_dir / "public" / "reference").exists()

    def test_draft_release_is_skipped(self, tmp_path):
        _, releases_dir = self._run(
            tmp_path, [_make_release("2150.13.0", draft=True)], set()
        )
        assert not (releases_dir / "2150-13-0.md").exists()
        assert not (releases_dir / "archived" / "2150-13-0.md").exists()

    def test_existing_top_level_notes_are_cleaned(self, tmp_path):
        _, releases_dir = self._run(tmp_path, [_make_release("1877.26")], {"1877.26"})
        stale = releases_dir / "9999-0-0.md"
        stale.write_text("stale")

        generate_release_notes_docs(
            tmp_path / "docs", [_make_release("1877.26")], {"1877.26"}
        )
        assert not stale.exists()

    def test_no_releases_returns_false(self, tmp_path):
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        assert not generate_release_notes_docs(docs_dir, [], set())
