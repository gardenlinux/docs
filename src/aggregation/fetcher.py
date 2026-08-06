"""Repository fetching for documentation aggregation."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Tuple

from .models import AggregateResult, RepoConfig
from .sphinx_builder import build_sphinx_markdown


class DocsFetcher:
    """Handles fetching documentation from remote or local repositories."""

    def __init__(self, project_root: Path, update_locks: bool = False):
        """
        Initialize fetcher.

        Args:
            project_root: Root directory of docs project
            update_locks: Whether we're in update-locks mode (allows commit mismatches)
        """
        self.project_root = project_root
        self.update_locks = update_locks

    def fetch(self, repo: RepoConfig, output_dir: Path) -> AggregateResult:
        """
        Fetch documentation for a repository.

        Args:
            repo: Repository configuration
            output_dir: Where to copy fetched files

        Returns:
            AggregateResult with success status and resolved commit
        """
        if repo.is_local:
            success = self._fetch_local(repo, output_dir)
            return AggregateResult(repo.name, success, None)
        else:
            success, commit = self._fetch_remote(repo, output_dir)
            return AggregateResult(repo.name, success, commit)

    def _fetch_remote(
        self,
        repo: RepoConfig,
        output_dir: Path,
    ) -> Tuple[bool, str | None]:
        """Fetch from remote repository using git sparse checkout."""
        temp_dir = Path(tempfile.mkdtemp())

        try:
            print(f"  Fetching from: {repo.url}")
            print(f"  Ref: {repo.ref}")
            if repo.root_files:
                print(f"  Root files: {', '.join(repo.root_files)}")
            print(f"  Output: {output_dir}")

            # Initialize git repository
            subprocess.run(
                ["git", "init"], check=True, capture_output=True, cwd=temp_dir
            )
            subprocess.run(
                ["git", "remote", "add", "origin", repo.url],
                check=True,
                capture_output=True,
                cwd=temp_dir,
            )

            # Enable sparse-checkout in cone-mode
            subprocess.run(
                ["git", "config", "core.sparseCheckout", "true"],
                check=True,
                capture_output=True,
                cwd=temp_dir,
            )

            # Fetch the ref (full history to support any locked commit)
            print("  Fetching repository...")
            subprocess.run(
                ["git", "sparse-checkout", "init", "--cone"],
                check=True,
                capture_output=True,
                cwd=temp_dir,
            )

            # Build sparse-checkout pattern
            sparse_patterns = self._build_sparse_patterns(repo)

            # Set sparse-checkout patterns
            subprocess.run(
                ["git", "sparse-checkout", "set"] + sparse_patterns,
                check=True,
                capture_output=True,
                cwd=temp_dir,
            )

            # Determine which commit to checkout:
            # - In update-locks mode: always checkout the ref (latest)
            # - In normal mode: use locked commit if available, otherwise checkout ref
            if self.update_locks or not repo.commit:
                fetch_depth_args = ["--depth", "1"]
                checkout_ref = repo.ref
            else:
                fetch_depth_args = ["--filter=blob:none"]
                checkout_ref = repo.commit

            print(f"  Fetching sparse checkout: {checkout_ref}")
            print(f"  Patterns: {', '.join(sparse_patterns)}")
            print(
                f"  Strategy: {'shallow' if '--depth' in fetch_depth_args else 'partial'}"
            )

            fetch_cmd = ["git", "fetch"] + fetch_depth_args + ["origin", checkout_ref]
            subprocess.run(fetch_cmd, check=True, capture_output=True, cwd=temp_dir)

            subprocess.run(
                ["git", "checkout", checkout_ref],
                check=True,
                capture_output=True,
                cwd=temp_dir,
            )

            # Get resolved commit hash
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
                cwd=temp_dir,
            )
            resolved_commit = result.stdout.strip()
            print(f"  Resolved commit: {resolved_commit}")
            # Copy docs to output directory
            # Copy docs to output directory (or build Sphinx Markdown first)
            docs_source = temp_dir / repo.docs_path
            if docs_source.exists():
                if repo.structure == "sphinx":
                    print(f"  Building Sphinx Markdown from {repo.docs_path}/")
                    sphinx_ok = build_sphinx_markdown(
                        temp_dir,
                        repo.docs_path,
                        output_dir,
                        target_map=repo.target_map or None,
                    )
                    if not sphinx_ok:
                        print(
                            f"  Warning: Sphinx build failed; falling back to raw docs copy"
                        )
                        self._copy_docs(docs_source, output_dir)
                else:
                    print(f"  Copying docs to {output_dir}")
                    self._copy_docs(docs_source, output_dir)
            else:
                print(
                    f"  Warning: docs_path '{repo.docs_path}' not found in repository"
                )

            # Copy root files if specified
            self._copy_root_files(temp_dir, repo.root_files, output_dir)

            print("  ✓ Fetch complete")
            return True, resolved_commit

        except subprocess.CalledProcessError as e:
            print(f"  Error: Git command failed: {e}", file=sys.stderr)
            if e.stderr:
                print(f"  {e.stderr.decode()}", file=sys.stderr)
            return False, None
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            return False, None
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _build_sparse_patterns(self, repo: RepoConfig) -> list[str]:
        """
        Build sparse-checkout patterns for a repo.

        Uses cone mode patterns which are directory based and not glob patterns.

        Args:
            repo: Repository configuration

        Returns:
            List of directory patterns for sparse-checkout
        """
        patterns: list[str] = []

        # Always include docs path
        if repo.docs_path:
            patterns.append(repo.docs_path)

        # Add root files if necessary
        if repo.root_files:
            for file_pattern in repo.root_files:
                cone_pattern = self._to_cone_pattern(file_pattern)
                if cone_pattern and cone_pattern not in patterns:
                    patterns.append(cone_pattern)

        return patterns

    def _to_cone_pattern(self, pattern: str) -> str | None:
        """
        Convert a glob pattern to a cone-mode sparse-checkout pattern.

        Cone mode doesn't support globs.

        Examples:
            "README.md" -> "README.md"  (file at root)
            "features/*/README.md" -> "features"  (directory)
            "features/foo/info.yaml" -> "features/foo"  (specific directory)
            "docs/**/*.md" -> "docs"  (directory)

        Args:
            pattern: Glob pattern from root_files

        Returns:
            Cone-compatible pattern as string
        """
        pattern = pattern.rstrip("/")

        # If globs, extract directory
        if any(char in pattern for char in ["*", "?", "[", "]"]):
            parts = pattern.split("/")
            for i, part in enumerate(parts):
                if any(char in part for char in ["*", "?", "[", "]"]):
                    # Return path up to the glob part
                    if i == 0:
                        # Glob at root level; Manually filter later.
                        return None
                    return "/".join(parts[:i])
            return pattern

        # No globs, check if file or directory
        # For cone pattern, include parent directory
        if "/" in pattern:
            # Path: return deepest directory
            parts = pattern.split("/")
            # If last part looks like a file with extension, return parent dir
            if "." in parts[-1]:
                return "/".join(parts[:-1]) if len(parts) > 1 else parts[-1]
            return pattern

        return pattern

    def _fetch_local(
        self,
        repo: RepoConfig,
        output_dir: Path,
    ) -> bool:
        """Fetch from local repository via direct filesystem copy."""
        try:
            # Resolve repo path (handle relative paths)
            repo_path = Path(repo.local_path)
            if not repo_path.is_absolute():
                repo_abs_path = (self.project_root / repo_path).resolve()
            else:
                repo_abs_path = repo_path.resolve()

            print(f"  Copying from: {repo_abs_path}")
            if repo.root_files:
                print(f"  Root files: {', '.join(repo.root_files)}")
            print(f"  Output: {output_dir}")

            if not repo_abs_path.exists():
                print(
                    f"  Error: Local repository not found: {repo_abs_path}",
                    file=sys.stderr,
                )
                return False

            # Copy docs directory (or build Sphinx Markdown first)
            docs_source = repo_abs_path / repo.docs_path
            if docs_source.exists():
                if repo.structure == "sphinx":
                    print(f"  Building Sphinx Markdown from {repo.docs_path}/")
                    sphinx_ok = build_sphinx_markdown(
                        repo_abs_path,
                        repo.docs_path,
                        output_dir,
                        target_map=repo.target_map or None,
                    )
                    if not sphinx_ok:
                        print(
                            f"  Warning: Sphinx build failed; falling back to raw docs copy"
                        )
                        self._copy_docs(docs_source, output_dir)
                else:
                    print(f"  Copying docs from {repo.docs_path}/")
                    self._copy_docs(docs_source, output_dir)
            else:
                print(
                    f"  Warning: docs_path '{repo.docs_path}' not found in local repository"
                )

            # Copy root files if specified
            self._copy_root_files(repo_abs_path, repo.root_files, output_dir)

            print("  ✓ Copy complete")
            return True

        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            return False

    @staticmethod
    def _copy_docs(source: Path, dest: Path) -> None:
        """
        Copy documentation directory contents.

        Args:
            source: Source docs directory
            dest: Destination directory
        """
        dest.mkdir(parents=True, exist_ok=True)

        # Copy all regular files and directories
        for item in source.iterdir():
            target = dest / item.name
            if item.is_file():
                shutil.copy2(item, target)
            elif item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)

        # Also copy hidden directories (like .media)
        for item in source.glob(".*"):
            if item.is_dir() and item.name not in [".", ".."]:
                target = dest / item.name
                shutil.copytree(item, target, dirs_exist_ok=True)

    @staticmethod
    def _copy_root_files(repo_root: Path, root_files: list, dest: Path) -> None:
        """
        Copy specified root-level files and directories from repository.

        Supports glob patterns like "features/*/*.md" to match specific files
        without copying entire directories.

        Args:
            repo_root: Root directory of the repository
            root_files: List of filenames/directories/patterns to copy
            dest: Destination directory
        """
        if not root_files:
            return

        print("  Copying root files")
        for filename in root_files:
            clean_name = filename.rstrip("/")

            if "*" in clean_name or "?" in clean_name or "[" in clean_name:
                matches = list(repo_root.glob(clean_name))
                if not matches:
                    print(f"    Warning: {filename} not found (no matches)")
                    continue

                for src in matches:
                    rel_path = src.relative_to(repo_root)
                    target = dest / rel_path
                    if src.is_dir():
                        try:
                            shutil.copytree(
                                src, target, dirs_exist_ok=True, symlinks=False
                            )
                            print(f"    ✓ {filename} -> {rel_path} (directory)")
                        except Exception as e:
                            print(f"    Warning: Failed to copy {rel_path}: {e}")
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, target)
                        print(f"    ✓ {filename} -> {rel_path}")
            else:
                src = repo_root / clean_name
                if src.exists():
                    target = dest / src.name
                    if src.is_dir():
                        try:
                            shutil.copytree(
                                src, target, dirs_exist_ok=True, symlinks=False
                            )
                            print(f"    ✓ {filename} (directory)")
                        except Exception as e:
                            print(f"    Warning: Failed to copy {filename}: {e}")
                    else:
                        shutil.copy2(src, target)
                        print(f"    ✓ {filename}")
                else:
                    print(f"    Warning: {filename} not found")
