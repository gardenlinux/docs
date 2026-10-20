---
title: "Contributing to the Garden Linux Documentation"
description: "Learn how to contribute to Garden Linux documentation — working with the aggregation system locally"
order: 5
related_topics:
  - /contributing/documentation/documentation_workflow.md
  - /contributing/documentation/writing_good_docs.md
  - /contributing/documentation/aggregation-architecture.md
  - /contributing/documentation/adding-repos.md
  - /contributing/documentation/ci-architecture.md
  - /contributing/documentation/ci-workflows-reference.md
  - /contributing/documentation/configuration.md
  - /contributing/documentation/technical.md
  - /contributing/documentation/testing.md
  - /contributing/documentation/vitepress-features.md
---

# Contributing to the Garden Linux Documentation

Garden Linux documentation is published at
**https://docs.gardenlinux.org/** and combines content from multiple
repositories into a unified documentation site.

## Working with the Documentation System Locally

For more substantial changes, (adding new pages, restructuring content, or
working on the aggregation system itself) you will want to set up the
documentation system locally.

### Prerequisites

- Python 3.x
- pnpm (for VitePress)
- virtualenv (optional)
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/gardenlinux/docs.git
cd docs
```

### Step 2: Install Dependencies

```bash
pnpm install
```

This installs VitePress and other Node.js dependencies needed to build the
documentation site.

:::tip Problems with installing Python Dependencies?

Potentially, your Linux distribution or other operating system might forbid you from installing
python dependencies system wide.

To go around this, it is wise practice to use a [virtual environment](https://www.w3schools.com/python/python_virtualenv.asp).

We use [`virtualenv`](https://virtualenv.pypa.io/en/latest/). Install virtualenv via your distributions package manager
or a method appropriate for your operating system.

Then, create the virtual environment and activate it.

```bash
virtualenv .venv && source .venv/bin/activate
```

afterwards, continue working like normal.

In the end, you can deactivate the environment using

```bash
deactivate
```
or closing the Terminal.
:::

### Step 3: Aggregate Documentation

#### From Remote Repositories (Production)

Aggregate from locked commits in `repos-config.json`:

```bash
make aggregate
```

This fetches documentation from the configured repositories at their locked
commit hashes.

:::info Add A GitHub API Token To Counter Rate Limiting

`make aggregate` also fetches every release from `gardenlinux/gardenlinux` via
the GitHub Releases API to generate per-release note pages and to validate
GLRD-listed minor releases. Set `GITHUB_TOKEN` before running `make aggregate`
to prevent rate-limiting:

```bash
export GITHUB_TOKEN=$(gh auth token)
make aggregate
```

:::tip
You can add the `export` statement to you Shell's configuration file to avoid having to re-export it in different sessions.
:::
:::

#### From Local Repositories (Development)

For local development, use `repos-config.local.json` with `file://` URLs:

```bash
make aggregate-local
```

This copies documentation from local repositories without using git.

### Step 4: Start the Development Server

```bash
make run
```

The documentation site will be available at `http://localhost:5173`.

### Step 5: Make Changes

As you work on documentation in source repositories:

1. Make changes to markdown files in source repos
2. Run `make aggregate-local` to update the aggregated docs
3. The dev server will hot-reload automatically

### Step 6: Build for Testing 

```bash
make build 
```

This creates a build in `docs/.vitepress/dist/` for testing purposes.

### Step 7: Build for Production

Once ready to deploy:

```bash
make publish
```

This runs certain transformation steps such as the automatic glossary and creates a production build in `docs/.vitepress/dist/`.

::: tip Note
Transformation will leave your local work tree "dirty" (with unstaged changes) as the automatic glossary will
replace all terms designates with shortcodes (e.g. `{glossary:*}`) with links to the respective glossary entry.
:::

## Common Workflows

### Updating a Single Repository

To re-aggregate only one repository without re-fetching all others:

```bash
make aggregate-repo-single REPO=gardenlinux
```

To re-aggregate a single repository at a specific ref or commit:

```bash
make aggregate-repo-single REPO=gardenlinux REF=feature/my-branch
make aggregate-repo-single REPO=gardenlinux REF=feature/my-branch COMMIT=abc123def
```

To apply a ref or commit override to one repository while re-aggregating all
repos (for example, to test a feature branch across the full docs tree):

```bash
make aggregate-repo REPO=gardenlinux REF=feature/my-branch
```

### Updating Lock Files

To fetch the latest commits and update `repos-config.json`:

```bash
make aggregate-update
```

### Running Tests

```bash
make test
```

## Project Structure

After aggregation, your docs directory will look like:

```
docs/
├── tutorials/             # Aggregated tutorials
├── how-to/                # Aggregated guides
├── explanation/           # Aggregated explanations
├── reference/             # Aggregated reference
└── contributing/          # Aggregated contributing docs
```

## Troubleshooting

### Clean Build

If you encounter issues, try a clean build:

```bash
make clean
make aggregate
make run
```

### Check Dependencies

Ensure all dependencies are installed:

```bash
pnpm install
python3 --version  # Should be 3.x
```

### Verify Configuration

Check that `repos-config.json` or `repos-config.local.json` is properly
configured. See the [configuration reference](./configuration.md) for details.

### GitHub API rate limit or fetch error

If `make aggregate` fails with a message like
`Could not fetch GitHub releases — HTTP 403 …`, the GitHub API rate limit is
exhausted or the request was rejected. Set `GITHUB_TOKEN` and retry:

```bash
export GITHUB_TOKEN=$(gh auth token)
make aggregate
```

See the [GitHub API token](#github-api-token) note under Step 3 for rate-limit
details.

## Related Topics

<RelatedTopics />
