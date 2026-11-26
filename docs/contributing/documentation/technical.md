---
title: "Documentation Aggregation Technical Reference"
description: "Source code documentation for the documentation aggregation system - modules, APIs, and implementation details"
order: 9
related_topics:
  - /contributing/documentation/documentation_workflow.md
  - /contributing/documentation/writing_good_docs.md
  - /contributing/documentation/aggregation-architecture.md
  - /contributing/documentation/adding-repos.md
  - /contributing/documentation/working-locally.md
  - /contributing/documentation/ci-architecture.md
  - /contributing/documentation/ci-workflows-reference.md
  - /contributing/documentation/configuration.md
  - /contributing/documentation/testing.md
  - /contributing/documentation/vitepress-features.md
github_org: gardenlinux
github_repo: docs
---

# Documentation Aggregation Technical Reference

Source code documentation for the documentation aggregation system.

## Source Code Structure

```text
src/
├── aggregate.py          # CLI entry point
├── migration_tracker.py  # Standalone utility
└── aggregation/          # Core package
    ├── __init__.py
    ├── config.py         # Config I/O
    ├── constants.py      # Shared constants (Mermaid theme, GitHub URL templates)
    ├── fetcher.py        # Git + local fetch
    ├── flavor_matrix.py  # Flavor matrix docs from flavors.yaml
    ├── github_api.py     # GitHub HTTP client (releases fetch, auth)
    ├── glrd.py           # GLRD subprocess wrapper (active versions, metadata)
    ├── models.py         # Data classes
    ├── release_notes.py  # Per-release note pages from GH data
    ├── releases.py       # Release tables from GLRD (filtered by GH tags)
    ├── sphinx_builder.py # Sphinx-to-Markdown builder for sphinx-structured repos
    ├── structure.py      # Directory transforms
    └── transformer.py    # Content transforms
```

## Module Reference

### `aggregation/models.py`

Data classes for type safety:

- **`RepoConfig`** — Repository configuration data class
- **`AggregateResult`** — Fetch result with commit hash

### `aggregation/config.py`

Configuration file handling:

- **`load_config()`** — Parse repos-config.json
- **`save_config()`** — Write updated config (commit locks)

### `aggregation/constants.py`

Shared constants for release-doc generation. Contains no functions; exposes
only module-level constants:

- **`GANTT_THEME`** — Mermaid Gantt chart theme variables using the Garden
  Linux color palette.
- **`GITHUB_BASE_URL`**, **`RELEASES_TAG_URL`**, **`COMMITS_URL`** — GitHub URL
  templates for the `gardenlinux/gardenlinux` repository.
- **`LIFECYCLE_LINKS`** — Anchor-link map for release lifecycle documentation
  sections.

### `aggregation/fetcher.py`

Repository fetching:

**`DocsFetcher`** — Main fetcher class

Methods:

- **`__init__(project_root, update_locks=False)`** — Initialize with optional
  commit lock updating
- **`fetch()`** — Fetch repository and return result with commit hash
- **`_fetch_remote()`** — Git sparse checkout from remote repository
- **`_fetch_local()`** — Filesystem copy from local repository
- **`_copy_docs()`** — Static method to copy docs directory
- **`_copy_root_files()`** — Static method to copy root-level files (e.g.,
  CONTRIBUTING.md)

### `aggregation/transformer.py`

Content transformation:

- **`rewrite_links()`** — Fix markdown links for cross-repository references
- **`quote_yaml_value()`** — YAML safety for front-matter values
- **`ensure_frontmatter()`** — Add or fix front-matter in markdown files
- **`parse_frontmatter()`** — Extract metadata from markdown front-matter
- **`fix_broken_project_links()`** — Validate and fix links to project mirrors

### `aggregation/github_api.py`

GitHub HTTP client for release data:

- **`GitHubAPIError`** — Exception raised on any GitHub API failure (network,
  non-2xx, rate-limit, or empty first page).
- **`get_json(url)`** — Fetch a single GitHub API URL and return the parsed
  JSON response. Uses `GH_COM_TOKEN` for api.github.com and `GH_ENTERPRISE_TOKEN`
  for `GH_ENTERPRISE_HOST` (`GITHUB_TOKEN` is a public-host-only alias).
  Hard-fails on non-2xx status and prevents cross-origin authenticated redirects.
- **`list_repo_releases(owner, repo, per_page=100)`** — Paginate through all
  releases for a repository and return the full list. Paginates until GitHub
  returns an empty page (uncapped). Hard-fails on any error or an empty first
  page.

This module is the single source of truth for GitHub HTTP calls in the
aggregation package. Future callers should use it rather than adding new
ad-hoc HTTP requests.

### `aggregation/glrd.py`

GLRD subprocess wrapper:

- **`run_glrd_json(args)`** — Run `glrd` with JSON output and return the parsed
  data. Returns `None` on any failure (binary not found, non-zero exit, JSON
  decode error).
- **`get_active_minor_versions()`** — Return the set of active minor-release
  version strings from GLRD (e.g. `{"1877.14", "2150.1.0"}`).

### `aggregation/sphinx_builder.py`

Sphinx-to-Markdown builder for repos configured with
`"structure": "sphinx"` in `repos-config.json`:

- **`build_sphinx_markdown(repo_dir, docs_path, output_dir, target_map=None)`**
  — Run `python -m sphinx -M markdown` on a fetched repository and copy the
  resulting Markdown into `output_dir` so the standard Transform/Structure
  stages can consume it. Injects VitePress frontmatter, carries over
  hand-written Markdown files that have a `github_target_path` frontmatter
  field, and strips Sphinx HTML anchors that break VitePress compatibility.
  Returns `True` on success, `False` on any failure. Requires `sphinx`,
  `sphinx-markdown-builder`, and any project-specific Sphinx extensions
  installed in the same Python environment as the aggregator.

### `aggregation/releases.py`

Release-table generation from GLRD data:

- **`generate_release_docs(docs_dir, existing_gh_tags)`** — Read GLRD release
  data and write per-release documentation pages. Only writes pages for
  releases whose normalized version string appears in `existing_gh_tags`.
- **`generate_release_table(releases_data, active_versions,
existing_gh_tags)`** — Build the release-status table. GLRD-listed rows that
  carry a `minor` version component are only emitted when their normalized
  version string appears in `existing_gh_tags`. Major-only rows are always
  emitted. Skipped rows are logged to `stderr`.

### `aggregation/release_notes.py`

Per-release note page generation:

- **`generate_release_notes_docs(docs_dir, releases)`** — Write one Markdown
  page per release from the pre-fetched `releases` list. Accepts the release
  list returned by `github_api.list_repo_releases()` and makes no network
  calls itself.

### `aggregation/flavor_matrix.py`

Flavor matrix documentation generator:

- **`get_flavor_list(gardenlinux_repo_dir)`** — Parse `flavors.yaml` in the
  fetched Garden Linux repository and return a per-architecture dict of flavor
  combinations. Returns `None` on failure.
- **`generate_flavor_matrix_docs(docs_dir, gardenlinux_repo_dir)`** — Generate
  the flavor matrix Markdown page by combining `get_flavor_list()` output with
  feature metadata from the Garden Linux `FeaturesParser`. Appends the
  generated table to the existing aggregated `reference/flavor-matrix.md` file.
  Returns `True` on success, `False` on any failure.

### `aggregation/structure.py`

Directory operations:

- **`copy_targeted_docs(source_dir, docs_dir, repo_name, media_dirs=None, root_files=None)`**
  — Copy files with `github_target_path` front-matter to specified locations
  - Handles nested media dirs (e.g., `tutorials/assets/`) by copying to same
    relative path
  - Handles root-level media dirs (e.g., `_static/`) by copying to common
    ancestor of targeted files
  - Supports scanning root_files for targeted placement
- **`verify_internal_links(source_dir, docs_dir, repo_name)`** — Verify that
  all internal relative links in shipped Markdown files resolve to files that
  were also shipped. Returns the number of broken links found (0 = success).
  Hard-fails aggregation when any shipped file links to a source-repo file that
  was not itself shipped.
- **`process_markdown_file()`** — Transform single markdown file (links,
  front-matter)
- **`process_all_markdown()`** — Batch process all markdown files in directory

### `aggregate.py`

CLI orchestration — Combines all modules into the complete aggregation workflow.

## Usage Example

Basic programmatic usage:

```python
from aggregation import load_config, DocsFetcher, process_all_markdown

# Load configuration
repos = load_config("repos-config.json")

# Initialize fetcher
fetcher = DocsFetcher(project_root)

# Fetch documentation
result = fetcher.fetch(repo, output_dir)

# Transform markdown files
process_all_markdown(target_dir, repo_name)
```

## Key Concepts

### Targeted Documentation

Files with `github_target_path` in their front-matter are automatically placed
at that exact path:

```yaml
---
github_target_path: "docs/tutorials/example.md"
---
```

The `copy_targeted_docs()` function scans all markdown files and copies those
with this front-matter to their specified locations.

### Link Rewriting

The `rewrite_links()` function transforms markdown links to work in the
aggregated site:

- Relative links within the same repo are maintained
- Cross-repository links are rewritten to point to the correct locations
- Links to project mirrors are validated

### Media Handling

Media directories specified in `media_directories` configuration are:

1. Discovered recursively in the source repository
2. Copied alongside their associated documentation
3. Placed according to whether they're nested (same relative path) or root-level
   (common ancestor)

### Commit Locking

When `update_locks=True` is passed to `DocsFetcher.__init__()`, the system:

1. Fetches from the `ref` (branch/tag)
2. Records the resolved commit hash
3. Updates `repos-config.json` with the lock

This ensures reproducible builds.

## Development

### Running Tests

See [Testing Reference](./testing.md) for details on the test suite.

### Adding New Transformation

To add a new transformation:

1. Add function to `transformer.py`
2. Call it from `process_markdown_file()` or `process_all_markdown()`
3. Add tests in `tests/unit/test_transformer.py`

### Adding New Structure Type

To add a new structure mapping type:

1. Add the corresponding logic to `structure.py`
2. Add corresponding structure key handling
3. Update configuration documentation

## Architecture Decisions

Key architectural decisions are documented in the source repository:

- Sparse git checkout for efficiency
- Front-matter-based targeting for flexibility
- Separate fetch/transform/structure stages for modularity

## Related Topics

<RelatedTopics />
