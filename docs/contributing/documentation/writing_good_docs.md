---
title: Documentation Quality Markers
description: Writing Good Documentation
order: 2
related_topics:
  - /contributing/documentation/documentation_workflow.md
  - /contributing/documentation/aggregation-architecture.md
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

# Documentation Quality Markers

Good documentation should follow concrete and actionable quality markers to be
as helpful and professional as possible.

These markers can roughly be split into required markers, that every
documentation submission should have, and those which are context dependent and
therefore optional.

Quality is enforced in two complementary ways:

- **Automated checks** run in CI and locally. The
  [Garden Linux Docs Quality (GLDQ)](#automated-quality-checks-gldq) tool
  verifies structural markers, and additional tools cover spelling, dead links,
  and inclusive language.
- **Human review** covers everything a machine cannot judge, such as technical
  accuracy, readability, and consistent terminology. The
  [Documentation Workflow](./documentation_workflow.md) describes who reviews and
  how.

For how to use the custom components and front-matter fields referenced
throughout this guide, see
[VitePress Features](./vitepress-features.md). To rework AI-generated phrasing,
use the [humanizer skill](/.agents/skills/humanizer/SKILL.md) (see
[AI-generated phrasing to avoid](#ai-generated-phrasing-to-avoid)).

## Automated Quality Checks (GLDQ)

Garden Linux Docs Quality (GLDQ) is a linter that checks documentation for the
structural markers described in this guide. It runs in CI on every pull request
with `--strict`, which treats warnings as failures and blocks merges until the
findings are resolved.

### Running GLDQ locally

Run GLDQ before opening a pull request:

```bash
# Report findings (warnings do not fail the run)
make docs-check

# Treat warnings as failures, matching CI
make docs-check-strict

# Call the tool directly on any path
python3 src/gldq.py docs/

# List every rule with its severity
python3 src/gldq.py --list-rules
```

Spelling, dead links, and inclusive language are checked by separate tools:
`make spelling`, `make linkcheck`, and `make woke`.

### Rules

GLDQ findings have one of two severities. An `error` always fails the run; a
`warning` fails only under `--strict` (and therefore in CI).

#### Front matter

| Rule | Severity | What it checks |
| --- | --- | --- |
| `FM-YAML` | error | Front matter must be valid YAML. |
| `FM-TITLE` | warning | Front matter must include a non-empty `title`. |
| `FM-DESC` | warning | Front matter must include a non-empty `description`. |
| `FM-ORDER` | warning | `order` must be an integer when present. |
| `FM-REPO` | error | Front matter must include `github_org` and `github_repo`. |
| `FM-RELATED` | error | `related_topics` must be a list of existing documents. |

#### Headings

| Rule | Severity | What it checks |
| --- | --- | --- |
| `H1-ONE` | warning | Document must have exactly one level-1 heading. |
| `H1-EMPTY` | error | Headings must not be empty. |
| `HEAD-SKIP` | warning | Heading levels must not be skipped. |

#### Code blocks

| Rule | Severity | What it checks |
| --- | --- | --- |
| `CODE-LANG` | warning | Fenced code blocks must declare a language. |
| `CODE-BALANCE` | error | Fenced code blocks must be closed. |

#### Media and links

| Rule | Severity | What it checks |
| --- | --- | --- |
| `IMG-ALT` | error | Images must have non-empty alt text. |
| `LINK-TEXT` | error | Links must use descriptive link text, not "click here". |
| `EMOJI` | warning | Emoji are not allowed outside code fences. |

#### Components

| Rule | Severity | What it checks |
| --- | --- | --- |
| `SECTION-INDEX` | error | Section index pages must include `<SectionIndex />`. |
| `RELATED-TOPICS-END` | error | `<RelatedTopics />` must be the last content block. |
| `RELATED-TOPICS-FM` | error | `<RelatedTopics />` requires `related_topics` in front matter. |
| `RELATED-TOPICS-PRESENT` | warning | Non-index pages should include `<RelatedTopics />`. |

#### Callouts

| Rule | Severity | What it checks |
| --- | --- | --- |
| `CALLOUT-INVALID-TYPE` | error | Container type must be `info`, `tip`, `warning`, `danger`, or `details`. |
| `CALLOUT-GITHUB-STYLE` | error | GitHub-style callouts are rejected; use VitePress `:::` syntax. |
| `CALLOUT-UNCLOSED` | error | VitePress containers must be closed with `:::`. |

### Suppressing and excluding findings

When a finding does not apply, suppress it inline with a comment rather than
leaving the whole file unchecked:

```markdown
<!-- gldq: disable-next-line EMOJI -->
<!-- gldq: disable EMOJI -->
<!-- gldq: disable-file CODE-LANG -->
```

`disable-next-line` affects the following line, `disable` affects the rest of
the file from that point, and `disable-file` affects the entire file. Each
directive takes one or more rule IDs.

Files that cannot be edited in this repository (for example aggregated content)
are handled by the rule-aware exclusion file `.gldq-exclude.yml`, which maps rule
patterns to path patterns. Prefer inline suppressions for authored content and
reserve the exclusion file for generated files.

## Required Markers

### Accuracy & Completeness

All documentation must be correct in an informational sense. All code and
commands need to be tested and any tutorials & guides that are meant to lead a
user through a process should be executed by the reviewer once to see if they do
what they were written for.

All code examples should:

- Be tested and verified to work
- Include expected output
- Cover common error cases where applicable
- Use realistic, representative examples

All documents should cover all the aspects of their respective topics and not
exclude edge cases even if they appear infrequent.

Each document should clearly state:

- Prerequisites (required knowledge, tools, or setup)
- Context (when and why this information is relevant)
- Next steps or related documentation

### Readability

One of the most important factors of good documentation is readability. This
means that good documents should have a clear structure separated by concise
headlines that are both a navigation aid and a thread through the
topic.

Another aspect of good readability is a well thought out **separation of
thoughts**. Ideally, every thought should have its own paragraph. This goes hand
in hand with keeping the sentence structure as short as possible and avoid
overly complex or nested sentences if possible.

Additional readability guidelines:

- Use active voice over passive voice
- Keep sentences focused (aim for 15-25 words)
- Use progressive disclosure (introduce simple concepts before complex ones)
- Break up long procedures into numbered steps

### Style & Language

All documentation should have a professional and inclusive tone. Gender-neutral
language (like they/them or role based nouns like "maintainer", "developer" or
"user") should be used. Language specific idioms common amongst native speakers
should be avoided and project specific abbreviations should always link to their
respective Glossary section.

Hand in hand with the last point goes formulating documents with **consistent
terminology**. To avoid confusion, especially in tutorials, certain terms like
"install" and "set up" should not be used as synonyms, but instead have their
own respective meanings.

Documentation should go into appropriate detail for the intended audience (i.e.
Users or Developers) and not omit any details or become vague when talking about
specific topics.

If a feature is not yet implemented or there are currently known bugs or Issues,
a "Known Issues" section should be appended to the bottom of the document
listing these issues and their corresponding GitHub issue if applicable.

Include expected output or other steps which the reader can use to verify
operation outcomes in any instructional guides.

Use examples liberally across the documentation for any document that advises
readers to action.

#### AI-generated phrasing to avoid

AI-assisted writing introduces recognizable patterns that reduce documentation
quality through repetition. Avoid these categories when authoring:

- Hype openers and filler adjectives (`unlock`, `seamlessly`, `robust`,
  `leverage`)
- Transitional bloat (`Moreover`, `It's worth noting`)
- Promotional flourish (`world-class`, `next-generation`, `game-changing`)
- Hedging and rhetorical-question openers (`In today's fast-paced world`,
  `Ever wondered...?`)
- Chatbot artifacts and sycophancy (`Certainly!`, `Great question!`,
  `excellent choice`)
- Copula avoidance (`serves as` where `is` fits), negative parallelisms
  (`not just ... but`), and synonym cycling for one concept
- Generic conclusions (`By following these steps`, `You are now ready to`)
- Emoji outside code fences (also enforced by the GLDQ `EMOJI` rule)

The [humanizer skill](/.agents/skills/humanizer/SKILL.md) is the single source
of truth for the full pattern catalog, each with a before-to-after example and a
minimal-rewrite workflow. See also
[Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing),
the [softaworks/agent-toolkit humanizer skill](https://github.com/softaworks/agent-toolkit/blob/3027f20f3181758385a1bb8c022d4041dfb4de84/skills/humanizer/SKILL.md),
and [blader/humanizer](https://github.com/blader/humanizer/blob/1b48564898e999219882660237fde01bf4843a0f/SKILL.md).

Filler words (`simply`, `just`, `easy`/`easily`, `actually`, `basically`,
`obviously`) are a separate category governed by the style guide's
banned-filler-word rule.

The "no vague polish" refusal policy applies for reviewers: contributors must
identify a specific pattern from the humanizer catalog when reworking phrasing.

### Usability & Accessibility

Every person browsing documentation has different means and needs. They look for
different information and access documentation through different means. Language barriers, cultural differences or disabilities may present barriers when
attempting to look for something in documentation.

There are a few things contributors can do to lower these barriers:

- Use descriptive link texts instead of a simple "click here"
- Images should have a descriptive alt text that explains what the image shows
- Headings should have a proper hierarchy to ease browsing (don't skip heading
  levels)
- Code examples should have syntax highlighting
- Navigation via keyboard must be possible across the site, the search bar
  should ideally be accessible via key combination
- In graphs and other visual media, **color alone must never be the only
  indicator of differences or importance** - use icons, labels, or patterns as
  well
  - In a similar vain: Important graphs and diagram should be **native format first** meaning a embedded format that can at least potentially be parsed by
    a screen reading application - such as `mermaid` - instead of a simple image.
- All links should be verified as working (no dead links)
- Links to external resources should specify version where applicable

### Discoverability

The best documentation is useless if no one can find it. All documents must be
discoverable on all index pages or navigation bars and be linked in the
appropriate context.

Documents should:

- Have clear, descriptive titles
- Be placed in the appropriate section (Tutorial, How-to, Explanation,
  Reference)
- Be cross-referenced from related documentation
- Include relevant keywords for search
- **Include the `<RelatedTopics />` component with appropriate frontmatter**

### Maintainability

Documentation should be structured to minimize maintenance burden:

- Follow the [single source of truth](/reference/adr/0038-public-by-default-documentation-policy) principle; don't duplicate information
  across multiple pages
- Include version information where relevant
- Clearly indicate ownership:
  - For subproject documentation, the maintainers of that subproject
    (identifiable via git blame) are responsible for updates
  - For documentation hub content (like these guides), the Documentation Lead
    owns maintenance if that role exists
- Use includes or references for content that appears in multiple places

### Using Custom Components

Garden Linux documentation includes custom VitePress components that should
be used appropriately:

- **`<SectionIndex />`**: Always use on section index pages (tutorials/index.md,
  how-to/index.md, etc.) to display child pages automatically
- **`<RelatedTopics />`**: Add at the end of content pages to link to related
  documentation
- **Front-matter**: Always include `title` and `description` fields; use
  `order` to control sort order in listings
- See [VitePress Features](vitepress-features.md) for complete documentation
  of available components and front-matter fields

## Conditional Markers

### Version Compatibility

Features that only apply to specific versions of Garden Linux or supporting
tools should be marked as such using markdown admonishments or any other
suitable formatting to make them stand out.

Breaking changes between versions should be indicated in an appropriately
colored warning or info box at the top of the document.

Version-specific content should include:

- Minimum version required
- Version where feature was introduced
- Deprecation warnings if applicable

## Checklist

The checklist is split by who verifies each item. The automated half is already
enforced by tooling, so do not tick it by hand; run the commands instead. The
human review half covers everything a machine cannot judge.

### Automated checks (enforced in CI)

Run these before opening a pull request. They fail the build if findings remain:

```bash
make docs-check-strict   # GLDQ structural markers
make spelling            # spelling
make linkcheck           # dead links
make woke                # inclusive language
```

`make docs-check-strict` covers, among others: image alt text
([`IMG-ALT`](#media-and-links)), descriptive link text
([`LINK-TEXT`](#media-and-links)), code block languages
([`CODE-LANG`](#code-blocks)), heading hierarchy
([`HEAD-SKIP`](#headings) and [`H1-ONE`](#headings)), emoji
([`EMOJI`](#media-and-links)), related topics
([`RELATED-TOPICS-PRESENT`](#components)), front matter
([`FM-*`](#front-matter)), and callout syntax ([`CALLOUT-*`](#callouts)). See the
[GLDQ rules](#rules) for the full list. Spelling, dead links, and inclusive
language are handled by `make spelling`, `make linkcheck`, and `make woke`.

### Human review checklist

A reviewer must confirm the items that tooling cannot verify:

- All code and commands are tested and working
- Prerequisites are clearly stated
- Expected output is shown for verification steps
- One main idea per paragraph
- Sentences are concise and use active voice
- Neutral and professional language throughout
- Consistent terminology (no synonym confusion)
- Project-specific abbreviations link to Glossary
- Color is not the only indicator in visual media
- Document is discoverable and cross-referenced in the right context
- Clear ownership indicated
- No AI-tell phrasing (see [AI-generated phrasing to avoid](#ai-generated-phrasing-to-avoid))

### Conditional Markers

- Version compatibility noted (if applicable)
- Breaking changes highlighted (if applicable)
- Known issues section included (if applicable)
- External dependencies documented (if applicable)

## Architecture Decisions

- [ADR 0038: Public-by-Default Documentation Policy](/reference/adr/0038-public-by-default-documentation-policy)
  — the formal policy backing the single-source-of-truth and no-duplication maintainability markers.

## Related Topics

<RelatedTopics />
