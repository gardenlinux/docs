---
title: "Documentation Auto Glossary"
description: "Automatically link common idioms to their glossary entry"
order: 13 
related_topics:
  - /contributing/documentation/documentation_workflow.md
  - /contributing/documentation/writing_good_docs.md
  - /contributing/documentation/adding-repos.md
  - /contributing/documentation/working-locally.md
  - /contributing/documentation/ci-architecture.md
  - /contributing/documentation/ci-workflows-reference.md
  - /contributing/documentation/configuration.md
  - /contributing/documentation/technical.md
  - /contributing/documentation/testing.md
  - /contributing/documentation/vitepress-features.md
github_org: gardenlinux
github_repo: docs
---

# Auto Glossary

The documentation system includes an automatic glossary linker that converts marked terms into links pointing to the glossary page.

## Quick Start

Mark terms in your documentation using the marker format:

```markdown
Deploy {glossary:Gardenlinux} on {glossary:AWS} using {glossary:KVM}.
```

After aggregation, this becomes:

```markdown
Deploy [Gardenlinux](/reference/glossary#gardenlinux) on [AWS](/reference/glossary#aws) using [KVM](/reference/glossary#kvm).
```

## Function

After aggregation, `make transform` runs through these steps:

1. Parse `docs/reference/glossary.md` to extract all level-3 headers as terms
2. Extract aliases from terms with parenthesized expansions (e.g., `ADR (Architecture Decision Record)`)
3. Scan all markdown files for glossary markers
4. Replace markers with markdown links to glossary anchors
5. Preserve code blocks, inline code, and existing links

## Marking Terms

Use the format where the term name matches a glossary entry:

```markdown
{glossary:AWS}
{glossary:Garden Linux}
{glossary:ADR (Architecture Decision Record)}
```

Term matching is case-insensitive but preserves your original formatting:

- Input: `{glossary:aws}` produces `[aws](/reference/glossary#aws)`
- Input: `{glossary:AWS}` produces `[AWS](/reference/glossary#aws)`

::: details Developer Information
The auto glossary system is designed to accept a new custom `entry_format` through which
the shortcode `{glossary:*}` can be replaced with a new custom pattern.

Check the source code for more information.
:::

## Protected Regions

The system leaves certain content unchanged:

- Fenced code blocks (triple backticks)
- Inline code (single backticks)
- Existing markdown links

Glossary markers inside these regions are not processed.

## Adding Glossary Terms

To add a new term:

1. Edit `docs/reference/glossary.md`
2. Add a level-3 header:

```markdown
### New Term Name

Definition of the term.
```

The anchor is generated automatically (lowercase, hyphens replace spaces). Reference it with the marker format in your documentation.

## Alias Support

Terms with parenthesized expansions create aliases automatically.

Given this glossary entry:

```markdown
### ADR (Architecture Decision Record)
```

The system creates:
- Main term: `ADR (Architecture Decision Record)`
- Alias: `Architecture Decision Record`
- Alias: `ADR`

All three can be used in markers and link to the same glossary entry.

## Auto-Linking



Auto-linking creates links for glossary terms without requiring explicit markers. This feature is disabled by default.

With auto-linking enabled, input text:

```
Deploy Gardenlinux on AWS using KVM virtualization.
```

Becomes:

```markdown
Deploy [Garden Linux](/reference/glossary#garden-linux) on [AWS](/reference/glossary#aws) using [KVM](/reference/glossary#kvm) virtualization.
```

Auto-linking rules:
- Links only the first occurrence of each term
- Matches longer terms first (`Garden Linux` before `Linux`)
- Case-insensitive matching
- Respects word boundaries
- Preserves code blocks and inline code
- Does not modify existing links

::: warning
This feature is disabled by default as it is highly experimental and intended for research work only.

**Contributors must not rely on this feature when contributing documentation.**
:::

## Makefile Targets

Process glossary links manually:

```bash
make glossary
```

Validate glossary structure:

```bash
make glossary-check
```

## Warnings

**Term not found:**

```
[Warning][auto-glossary] Term 'xyz' not found in glossary (referenced in file.md)
```

The marker remains unchanged. Add the term to the glossary, fix the spelling, or remove the marker.

**Anchor collision:**

```
[Warning][auto-glossary] Anchor collision detected:
  'Term 1' and 'Term 2' both generate anchor 'term-1-2'
```

Rename one of the terms in the glossary.

## Anchor Generation

Terms are converted to VitePress-compatible anchors:

- Convert to lowercase
- Replace spaces and special characters with hyphens
- Collapse consecutive hyphens
- Strip leading and trailing hyphens
- Normalize Unicode to ASCII

Examples:
- `AWS` becomes `aws`
- `Garden Linux` becomes `garden-linux`
- `ADR (Architecture Decision Record)` becomes `adr-architecture-decision-record`

## Technical Reference

Module location: `src/aggregation/auto_glossary.py`

Main components:
- `AutoGlossary` class for glossary processing
- `process_glossary_links()` function for batch processing
- `GLOSSARY_ENTRY_FORMAT` constant defining the default marker format

Integration points:
- Runs as part of `src/aggregate.py` after release notes generation
- Makefile provides `glossary` and `glossary-check` targets

## Testing

Run the test suite:

```bash
python3 -m pytest tests/unit/test_auto_glossary*.py tests/unit/test_generate_anchor.py -v
```

Test coverage includes format validation, anchor generation, alias extraction, auto-linking, and integration tests.
