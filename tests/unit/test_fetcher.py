"""Unit tests for fetcher module."""

from pathlib import Path

from aggregation.fetcher import DocsFetcher
from aggregation.models import RepoConfig


class TestSparseCheckoutPatternGeneration:
    """Test sparse-checkout pattern building."""

    def test_build_sparse_patterns_simple_path(self):
        fetcher = DocsFetcher(Path("."))
        repo = RepoConfig(
            name="test",
            url="https://github.com/test/repo",
            docs_path="docs",
            ref="main",
        )

        patterns = fetcher._build_sparse_patterns(repo)

        assert patterns == ["docs"]

    def test_build_sparse_patterns_with_root_files(self):
        fetcher = DocsFetcher(Path("."))
        repo = RepoConfig(
            name="test",
            url="https://github.com/test/repo",
            docs_path="docs",
            ref="main",
            root_files=["README.md", "LICENSE"],
        )

        patterns = fetcher._build_sparse_patterns(repo)

        assert "docs" in patterns
        assert "README.md" in patterns
        assert "LICENSE" in patterns

    def test_build_sparse_patterns_with_glob_patterns(self):
        fetcher = DocsFetcher(Path("."))
        repo = RepoConfig(
            name="test",
            url="https://github.com/test/repo",
            docs_path="docs",
            ref="main",
            root_files=["features/*/README.md", "features/*/info.yaml"],
        )
        patterns = fetcher._build_sparse_patterns(repo)

        assert "docs" in patterns
        assert "features" in patterns
        assert patterns.count("features") == 1

    def test_build_sparse_patterns_no_duplicates(self):
        fetcher = DocsFetcher(Path("."))
        repo = RepoConfig(
            name="test",
            url="https://github.com/test/repo",
            docs_path="docs",
            ref="main",
            root_files=["docs/extra.md", "docs/subfolder/file.md"],
        )

        patterns = fetcher._build_sparse_patterns(repo)

        assert patterns.count("docs") == 1


class TestConePatternConversion:
    def test_to_cone_pattern_simple_file(self):
        """Test conversion of simple filename at root."""
        fetcher = DocsFetcher(Path("."))

        result = fetcher._to_cone_pattern("README.md")

        assert result == "README.md"

    def test_to_cone_pattern_directory(self):
        """Test conversion of directory path."""
        fetcher = DocsFetcher(Path("."))

        result = fetcher._to_cone_pattern("features")

        assert result == "features"

    def test_to_cone_pattern_file_in_directory(self):
        """Test conversion of file path."""
        fetcher = DocsFetcher(Path("."))

        result = fetcher._to_cone_pattern("features/foo/info.yaml")

        assert result == "features/foo"

    def test_to_cone_pattern_glob_wildcard(self):
        """Test conversion of glob pattern with wildcard."""
        fetcher = DocsFetcher(Path("."))

        result = fetcher._to_cone_pattern("features/*/README.md")

        assert result == "features"

    def test_to_cone_pattern_double_wildcard(self):
        """Test conversion of glob pattern with double wildcard."""
        fetcher = DocsFetcher(Path("."))

        result = fetcher._to_cone_pattern("docs/**/*.md")

        assert result == "docs"

    def test_to_cone_pattern_root_glob_returns_none(self):
        """Test that glob at root level returns None."""
        fetcher = DocsFetcher(Path("."))

        result = fetcher._to_cone_pattern("*.md")

        assert result is None

    def test_to_cone_pattern_question_mark(self):
        """Test conversion of pattern with ? wildcard."""
        fetcher = DocsFetcher(Path("."))

        result = fetcher._to_cone_pattern("features/foo?/README.md")

        assert result == "features"

    def test_to_cone_pattern_bracket_glob(self):
        """Test conversion of pattern with bracket glob."""
        fetcher = DocsFetcher(Path("."))

        result = fetcher._to_cone_pattern("features/[ab]*/README.md")

        assert result == "features"

    def test_to_cone_pattern_trailing_slash(self):
        """Test that trailing slashes are removed."""
        fetcher = DocsFetcher(Path("."))

        result = fetcher._to_cone_pattern("features/")

        assert result == "features"

    def test_to_cone_pattern_nested_path(self):
        """Test conversion of nested directory path."""
        fetcher = DocsFetcher(Path("."))

        result = fetcher._to_cone_pattern("a/b/c/d")

        assert result == "a/b/c/d"

    def test_to_cone_pattern_nested_file(self):
        """Test conversion of nested file path."""
        fetcher = DocsFetcher(Path("."))

        result = fetcher._to_cone_pattern("a/b/c/file.txt")

        assert result == "a/b/c"
