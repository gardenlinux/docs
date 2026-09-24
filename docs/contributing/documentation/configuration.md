---
title: "Documentation Aggregation Configuration Reference"
description: "Complete reference for repos-config.json and repos-config.local.json configuration options"
order: 8
related_topics:
  - /contributing/documentation/documentation_workflow.md
  - /contributing/documentation/writing_good_docs.md
  - /contributing/documentation/aggregation-architecture.md
  - /contributing/documentation/adding-repos.md
  - /contributing/documentation/working-locally.md
  - /contributing/documentation/ci-architecture.md
  - /contributing/documentation/ci-workflows-reference.md
  - /contributing/documentation/technical.md
  - /contributing/documentation/testing.md
  - /contributing/documentation/vitepress-features.md
---

# Documentation Aggregation Configuration Reference

Complete reference for configuring the documentation aggregation system.

## Configuration Files

### `repos-config.json`

Main configuration file for production aggregation. Uses git URLs and commit
locks.

**Location:** Project root

### `repos-config.local.json`

Development configuration file for local testing. Uses `file://` URLs to avoid
git operations.

**Location:** Project root

## Configuration Structure

```json
{
  "repos": [
    {
      "name": "repository-name",
      "url": "https://github.com/org/repo",
      "ref": "main",
      "commit": "abc123...",
      "root_files": ["README.md"],
      "structure": "flat",
      "media_directories": [".media", "assets"]
    }
  ]
}
```

## Field Reference

### Required Fields

#### `name`

- **Type:** String
- **Description:** Unique identifier for the repository
- **Example:** `"gardenlinux"`, `"builder"`, `"python-gardenlinux-lib"`
- **Notes:** Used in generated paths and logging

#### `url`

- **Type:** String (URL or file path)
- **Description:** Repository location
- **Examples:**
  - Git: `"https://github.com/gardenlinux/gardenlinux"`
  - Local: `"file://../gardenlinux"`
- **Notes:** For local development, use `file://` URLs in
  `repos-config.local.json`

#### `docs_path`

- **Type:** String
- **Description:** Path to documentation directory within the repository
- **Examples:** `"docs"`, `"documentation"`, `"."` (for root)
- **Default:** `"docs"` (may be omitted when the value is `"docs"`)
- **Notes:** Relative to repository root; content of this directory is copied

#### `ref`

- **Type:** String
- **Description:** Git reference to fetch (branch, tag, or commit)
- **Examples:** `"main"`, `"v1.0.0"`
- **Notes:** Required for git URLs; ignored for `file://` URLs

### Optional Fields

#### `commit`

- **Type:** String (commit hash)
- **Description:** Lock to a specific commit for reproducible builds
- **Example:** `"abc123def456..."`
- **Default:** Not used (fetches from `ref`)
- **Notes:** Generated automatically with `make aggregate-update`

#### `root_files`

- **Type:** Array of strings
- **Description:** Root-level files to copy (e.g., README.md, CONTRIBUTING.md)
- **Example:** `["README.md", "CONTRIBUTING.md", "LICENSE"]`
- **Default:** `[]` (no root files copied)
- **Notes:** Files can have `github_target_path` front-matter for targeted
  placement

#### `structure`

- **Type:** String
- **Description:** How to reorganize directory structure
- **Options:**
  - `"flat"` — Copy all files as-is
  - `"sphinx"` — Sphinx documentation structure
- **Default:** `"flat"`

#### `media_directories`

- **Type:** Array of strings
- **Description:** Directory names to treat as media/assets
- **Example:** `[".media", "assets", "_static", "images"]`
- **Default:** `[".media", "assets"]`
- **Notes:**
  - Searched recursively in source repository
  - Nested media dirs (e.g., `tutorials/assets/`) copied to same relative path
  - Root-level media dirs (e.g., `_static/`) copied to common ancestor of
    targeted files

## Complete Example

```json
{
  "repos": [
    {
      "name": "gardenlinux",
      "url": "https://github.com/gardenlinux/gardenlinux",
      "ref": "main",
      "commit": "c4b1d8d7f878fcb3e779315d28e35fcb19ae4dfb",
      "root_files": ["CONTRIBUTING.md", "SECURITY.md"]
    },
    {
      "name": "builder",
      "url": "https://github.com/gardenlinux/builder",
      "ref": "main",
      "commit": "b10476ad8c46130f310e36daa42c6e2c14fb51a9"
    },
    {
      "name": "python-gardenlinux-lib",
      "url": "https://github.com/gardenlinux/python-gardenlinux-lib",
      "ref": "main",
      "commit": "9142fccc3d83ab51759db7d328fa19166bc1df63",
      "structure": "sphinx",
      "target_map": {
        "cli.md": "reference/python-gardenlinux-lib-cli.md",
        "api.md": "reference/python-gardenlinux-lib-api.md"
      }
    }
  ]
}
```

## Environment-Specific Configuration

### Production (`repos-config.json`)

- Use HTTPS git URLs
- Include `commit` locks for reproducibility
- Use stable branches for `ref`

### Development (`repos-config.local.json`)

- Use `file://` URLs for local repos
- Omit `commit` field (not used for local)
- Omit `ref` field (not needed for file://)
- Keep structure and other settings consistent with production

**Example local config:**

```json
{
  "repos": [
    {
      "name": "gardenlinux",
      "url": "file://../gardenlinux",
      "root_files": ["CONTRIBUTING.md", "SECURITY.md"]
    }
  ]
}
```

## Common Configuration Patterns

### Minimal Configuration

Simplest configuration for a flat repository:

```json
{
  "name": "my-repo",
  "url": "https://github.com/org/my-repo",
  "ref": "main"
}
```

### With Targeted Documentation

Repository using `github_target_path` front-matter:

```json
{
  "name": "my-repo",
  "url": "https://github.com/org/my-repo",
  "ref": "main",
  "media_directories": ["assets", "_static"]
}
```

Then in your markdown files:

```yaml
---
title: "My Tutorial"
github_target_path: "docs/tutorials/my-tutorial.md"
---
```

## Front-Matter Fields

### Aggregation-Specific Fields

When using `github_target_path` for aggregated content, you can include additional metadata:

- **`github_instance`**: Base URL of the GitHub instance (default: `"https://github.com"`).
- **`github_org`**: Organization name (e.g., `"gardenlinux"`)
- **`github_repo`**: Repository name (e.g., `"gardenlinux"`)
- **`github_source_path`**: Original file path in source repo (e.g.,
  `"docs/tutorial.md"`)
- **`github_branch`**: Branch name for edit links (default: `"main"`)

These fields enable "Edit this page on GitHub" links for aggregated content.

### Page Display Fields

For general page display and component configuration fields (such as `title`,
`description`, `order`, `overviewDescriptions`, and `related_topics`), see
[VitePress Features](vitepress-features.md).

## Related Topics

<RelatedTopics />
