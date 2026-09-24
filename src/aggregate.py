#!/usr/bin/env python3
"""
Unified documentation aggregation script for docs

This script orchestrates documentation aggregation from multiple repositories.
All heavy lifting is done by the aggregation package modules.
"""

import argparse
import sys
import tempfile
from pathlib import Path

from aggregation import DocsFetcher, copy_targeted_docs, load_config, save_config
from aggregation.flavor_matrix import generate_flavor_matrix_docs
from aggregation.github_api import GitHubAPIError, list_repo_releases
from aggregation.release_notes import generate_release_notes_docs
from aggregation.releases import generate_release_docs
from aggregation.structure import verify_internal_links


def transform_repo_docs(
    repo,
    docs_dir: Path,
    temp_dir: Path,
) -> bool:
    """Transform documentation for a single repository."""
    repo_name = repo.name
    print(f"\n{'='*60}")
    print(f"Transforming docs for: {repo_name}")
    print(f"{'='*60}")

    source_dir = temp_dir / repo_name

    # Step 1: Copy files with 'github_target_path:' frontmatter
    print(f"\nStep 1: Processing targeted files...")
    copy_targeted_docs(
        str(source_dir),
        str(docs_dir),
        repo_name,
        repo.media_directories,
        repo.root_files,
    )

    # Step 2: Verify internal links in shipped files
    print(f"\nStep 2: Verifying internal links...")
    link_errors = verify_internal_links(
        str(source_dir),
        str(docs_dir),
        repo_name,
    )
    if link_errors > 0:
        print(
            f"  [ERROR] {link_errors} unshipped link(s) found in {repo_name}. "
            "Add github_target_path to the linked files or remove the links."
        )
        return False

    print(f"\n✓ Transformation complete for {repo_name}")
    return True


def aggregate_repo(
    repo,
    docs_dir: Path,
    temp_dir: Path,
    fetcher: DocsFetcher,
) -> tuple:
    """
    Aggregate documentation for a single repository.

    Returns:
        Tuple of (success, resolved_commit_hash)
    """
    print(f"\n{'='*60}")
    print(f"Aggregating: {repo.name}")
    print(f"{'='*60}")

    # Create output directory for this repo
    repo_output_dir = temp_dir / repo.name
    repo_output_dir.mkdir(parents=True, exist_ok=True)

    # Fetch the repository
    result = fetcher.fetch(repo, repo_output_dir)

    if not result.success:
        print(f"✗ Failed to fetch {repo.name}")
        return False, result.resolved_commit

    # Transform the fetched docs
    transform_success = transform_repo_docs(repo, docs_dir, temp_dir)

    if not transform_success:
        print(f"✗ Failed to transform {repo.name}")
        return False, result.resolved_commit

    return True, result.resolved_commit


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Aggregate documentation from multiple repositories",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Aggregate all repositories (default)
  %(prog)s

  # Aggregate all repositories (explicit)
  %(prog)s --all

  # Aggregate all repos, applying overrides to one repo (used in CI)
  %(prog)s --repo gardenlinux --override-ref feature/my-docs --override-commit abc123def

  # Aggregate only a single repository
  %(prog)s --repo gardenlinux --single

  # Update commit locks for all repos
  %(prog)s --update-locks

  # Update commit lock for a single repo only
  %(prog)s --repo gardenlinux --single --update-locks
        """,
    )

    parser.add_argument(
        "--config",
        default="repos-config.json",
        help="Path to repos-config.json (default: repos-config.json)",
    )
    parser.add_argument(
        "--docs-dir",
        default="docs",
        help="Path to docs directory (default: docs)",
    )
    parser.add_argument(
        "--repo",
        help="Scope overrides to this repository; required when --single is used",
    )
    parser.add_argument(
        "--update-locks",
        action="store_true",
        help="Update commit locks: fetch and update config with resolved commit hashes",
    )
    parser.add_argument(
        "--override-ref",
        help="Override ref for the repo specified by --repo",
    )
    parser.add_argument(
        "--override-commit",
        help="Override commit for the repo specified by --repo",
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--all",
        action="store_true",
        help="Aggregate all repositories (default behaviour; explicit alias)",
    )
    mode_group.add_argument(
        "--single",
        action="store_true",
        help="Aggregate only the repository specified by --repo",
    )

    args = parser.parse_args()

    # Validate argument combinations
    if args.single and not args.repo:
        parser.error("--single requires --repo NAME")
    if (args.override_ref or args.override_commit) and not args.repo:
        parser.error("--override-ref/--override-commit require --repo NAME")

    # Determine script directory
    script_dir = Path(__file__).parent.resolve()
    project_root = script_dir.parent

    # Resolve paths
    # Config files are in project root, not in src/
    if not Path(args.config).is_absolute():
        config_path = project_root / args.config
    else:
        config_path = Path(args.config)

    if not Path(args.docs_dir).is_absolute():
        docs_dir = project_root / args.docs_dir
    else:
        docs_dir = Path(args.docs_dir)

    # Load configuration
    print(f"{'='*60}")
    print("Garden Linux Documentation Aggregation")
    print(f"{'='*60}\n")
    print(f"Configuration: {config_path}")
    print(f"Docs directory: {docs_dir}")
    if args.single and args.repo:
        print(f"Single-repo mode: {args.repo}")
    elif args.repo:
        print(f"Override scoped to: {args.repo}")
    if args.update_locks:
        print("Update commit locks: ENABLED")
    print()

    repos = load_config(str(config_path))

    # Apply overrides if specified
    if args.repo and (args.override_ref or args.override_commit):
        for repo in repos:
            if repo.name == args.repo:
                if args.override_ref:
                    repo.ref = args.override_ref
                    print(f"Override ref for {repo.name}: {args.override_ref}")
                if args.override_commit:
                    repo.commit = args.override_commit
                    print(f"Override commit for {repo.name}: {args.override_commit}")
                break
        else:
            parser.error(
                f"Repository '{args.repo}' not found in config; "
                "cannot apply --override-ref/--override-commit"
            )
    elif args.repo:
        # --repo without overrides: validate the name exists when --single is used
        # (filter will silently aggregate nothing if the name is wrong)
        repo_names = {repo.name for repo in repos}
        if args.repo not in repo_names:
            if args.single:
                parser.error(f"Repository '{args.repo}' not found in config")
            else:
                print(f"WARNING: Repository '{args.repo}' not found in config")

    # Create temporary directory for fetched docs
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        print(f"Temporary directory: {temp_dir}\n")

        # Initialize fetcher
        fetcher = DocsFetcher(project_root, update_locks=args.update_locks)

        # Track resolved commits for locking
        resolved_commits = {}
        success_count = 0
        fail_count = 0

        # Aggregate each repository
        gardenlinux_temp_dir = None
        for repo in repos:
            # Filter to a single repo when --single is set
            if args.single and repo.name != args.repo:
                continue

            success, resolved_commit = aggregate_repo(
                repo,
                docs_dir,
                temp_dir,
                fetcher,
            )

            if success:
                success_count += 1
                if resolved_commit:
                    resolved_commits[repo.name] = resolved_commit
                if repo.name == "gardenlinux":
                    gardenlinux_temp_dir = temp_dir / repo.name
            else:
                fail_count += 1

        # Update config with resolved commits if locking
        if args.update_locks and resolved_commits:
            print(f"\n{'='*60}")
            print("Updating config with resolved commits...")
            print(f"{'='*60}\n")

            for repo in repos:
                if repo.name in resolved_commits:
                    repo.commit = resolved_commits[repo.name]
                    print(f"  {repo.name}: {resolved_commits[repo.name]}")

            save_config(str(config_path), repos)
            print(f"\n✓ Config updated: {config_path}")

        # Generate flavor matrix documentation after all repos are aggregated
        # Use the gardenlinux temp dir (still available inside the with block)
        if gardenlinux_temp_dir and gardenlinux_temp_dir.exists():
            print(f"\n{'='*60}")
            print("Generating flavor matrix documentation...")
            print(f"{'='*60}\n")
            generate_flavor_matrix_docs(docs_dir, gardenlinux_temp_dir)

    # Fetch all GitHub releases up front — used by both release-doc generators.
    # Hard-fail here rather than inside the generators so the earlier repo-
    # aggregation results are still printed before we exit non-zero.
    print(f"\n{'='*60}")
    print("Fetching GitHub releases...")
    print(f"{'='*60}\n")
    try:
        gh_releases = list_repo_releases("gardenlinux", "gardenlinux")
    except GitHubAPIError as exc:
        print(
            f"\nError: Could not fetch GitHub releases — {exc}\n"
            "Hint: set GITHUB_TOKEN to avoid rate-limit issues: "
            "export GITHUB_TOKEN=$(gh auth token)",
            file=sys.stderr,
        )
        return 1
    existing_gh_tags = {r["tag_name"].lstrip("v") for r in gh_releases}
    print(
        f"  Fetched {len(gh_releases)} GitHub release(s), {len(existing_gh_tags)} unique tag(s)"
    )

    # Generate release documentation from GLRD
    print(f"\n{'='*60}")
    print("Generating release documentation...")
    print(f"{'='*60}\n")
    generate_release_docs(docs_dir, existing_gh_tags)

    # Generate release notes from pre-fetched GitHub releases
    print(f"\n{'='*60}")
    print("Generating release notes from GitHub...")
    print(f"{'='*60}\n")
    generate_release_notes_docs(docs_dir, gh_releases)

    # Summary
    print(f"\n{'='*60}")
    print("Documentation aggregation complete!")
    print(f"{'='*60}\n")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")

    print("\nNext steps:")
    print("  1. Review the changes in docs/")
    print("  2. Run 'make run' or 'pnpm run docs:dev' to preview")
    print("  3. Commit the changes if satisfied")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
