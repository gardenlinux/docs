---
title: "Adding Repositories to Documentation Aggregation"
description: "Guide for adding new repositories to the documentation aggregation system"
order: 4
related_topics:
  - /contributing/documentation/documentation_workflow.md
  - /contributing/documentation/writing_good_docs.md
  - /contributing/documentation/aggregation-architecture.md
  - /contributing/documentation/working-locally.md
  - /contributing/documentation/ci-architecture.md
  - /contributing/documentation/ci-workflows-reference.md
  - /contributing/documentation/configuration.md
  - /contributing/documentation/technical.md
  - /contributing/documentation/testing.md
  - /contributing/documentation/vitepress-features.md
---

# Adding Repositories to Documentation Aggregation

This guide explains how to add a new repository to the documentation aggregation
system.

## Prerequisites

- Access to the repository you want to add
- Understanding of the repository's documentation structure
- Edit access to `repos-config.json`

## Step 1: Add Repository Configuration

Edit `repos-config.json` and add a new entry to the `repos` array:

```json
{
  "name": "new-repo",
  "url": "https://github.com/gardenlinux/new-repo",
  "docs_path": "docs",
  "ref": "main",
  "structure": "flat"
}
```

### Required Fields

- **`name`**: Unique identifier for the repository
- **`url`**: Git URL or `file://` path for local development
- **`docs_path`**: Path to docs directory within the repository. Set explicitly
  for every repository in `repos-config.json` (defaults to `"docs"` if omitted,
  but do not rely on the default)
- **`ref`**: Git branch or tag to fetch from

### Optional Fields

- **`commit`**: Lock to a specific commit hash for reproducibility
- **`root_files`**: List of root-level files to copy (e.g.,
  `["README.md", "CONTRIBUTING.md"]`)
- **`docs_paths`**: Explicit override for the documentation-relevant glob
  patterns used by the documentation CI to detect documentation changes. By
  default this is derived as `["<docs_path>/**", ...root_files]`; only set it
  when a repository's documentation paths differ from that default (e.g.
  `daily`)
- **`structure`**: Directory mapping strategy (`"flat"` or `"sphinx"`; see below)
- **`media_directories`**: List of media directories to copy (e.g.,
  `[".media", "_static", "assets"]`)

## Step 3: Configure Targeted Documentation

To have files automatically placed into the main Diataxis structure, add
`github_target_path` front-matter to markdown files in the source repository:

```markdown
---
title: "Example Guide"
github_target_path: "docs/how-to/example-guide.md"
---

# Example Guide

Content here...
```

Files with `github_target_path` will be copied to that exact location in the
site. Source-repo files without `github_target_path` are excluded from the
built site entirely.

## Step 2: Choose a Structure Strategy

### Flat Structure

Copy all docs files as-is without reorganization:

```json
"structure": "flat"
```

### Sphinx Structure

For Sphinx-generated documentation:

```json
"structure": "sphinx"
```

## Step 3: Test with Local Configuration

Create or edit `repos-config.local.json` for local testing:

```json
{
  "repos": [
    {
      "name": "new-repo",
      "url": "file://../new-repo"
    }
  ]
}
```

Then test aggregation:

```bash
make aggregate-local
```

## Step 4: Verify the Output

Check that targeted files landed in the correct Diataxis section:

```bash
ls -la docs/tutorials/
ls -la docs/how-to/
```

## Step 5: Lock the Commit (Production)

For production, lock to a specific commit:

```bash
# This fetches only the new repo and updates repos-config.json with its commit hash
make aggregate-update-repo-single REPO=new-repo
```

Or manually add the commit hash:

```json
{
  "name": "new-repo",
  "url": "https://github.com/gardenlinux/new-repo",
  "docs_path": "docs",
  "ref": "main",
  "commit": "abc123def456...",
  "structure": "flat"
}
```

## Step 6: Install the Documentation CI Caller Workflow

Add a thin caller workflow at `.github/workflows/docs-check.yml` in the
repository. It delegates all documentation CI (change detection, quality checks,
the merge gate, and the notify/commit-lock dispatch) to the reusable
orchestrator in `gardenlinux/docs`:

```yaml
name: Documentation Quality Check

on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened, closed]
  push:
    branches: [main]

jobs:
  docs:
    uses: gardenlinux/docs/.github/workflows/aggregated-repo-docs.yml@main
    with:
      repo: new-repo
    secrets: inherit
```

Replace `new-repo` with the repository's `name` from `repos-config.json` and
adjust the branch to the repository's default branch. See
[CI Workflows Reference](./ci-workflows-reference.md) for details and required
secrets.

## Advanced Configuration

### Media Directories

Automatically copy media directories alongside documentation:

```json
{
  "name": "new-repo",
  "media_directories": [".media", "assets", "_static"]
}
```

The system will:

- Find all instances of these directories recursively
- Copy nested media dirs (e.g., `tutorials/assets/`) to the same relative path
- Copy root-level media dirs (e.g., `_static/`) to the common ancestor of
  targeted files

### Root Files

Copy root-level files (like README.md or CONTRIBUTING.md):

```json
{
  "name": "new-repo",
  "root_files": ["README.md", "CONTRIBUTING.md", "LICENSE"]
}
```

These files can also have `github_target_path` front-matter for targeted
placement.

## Complete Example

Here's a complete configuration:

```json
{
  "name": "example-tool",
  "url": "https://github.com/gardenlinux/example-tool",
  "docs_path": "documentation",
  "ref": "main",
  "commit": "1234567890abcdef",
  "root_files": ["README.md"],
  "structure": "flat",
  "media_directories": [".media", "images"]
}
```
The `docs_path` field defaults to `"docs"` and may be omitted when the documentation lives in a `docs/` directory.

## Troubleshooting

### Files Not Appearing

- Verify `docs_path` points to the correct directory
- Ensure `github_target_path` front-matter is correct

### Media Not Copied

- Add media directory names to `media_directories`
- Check that media dirs exist in the source repository

### Links Broken

- The transformer attempts to rewrite links automatically
- Check that relative links in source docs are correct
- Review `src/aggregation/transformer.py` for link rewriting logic

## Related Topics

<RelatedTopics />
