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
---

# Documentation Quality Markers

Good documentation should follow concrete and actionable quality markers to be
as helpful and professional as possible.

These markers can roughly be split into required markers, that every
documentation submission should have, and those which are context dependent and
therefore optional.

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

AI-assisted writing introduces recognizable patterns that reduce documentation quality. Avoid these categories when authoring (see also [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), [softaworks/agent-toolkit humanizer skill](https://github.com/softaworks/agent-toolkit/blob/3027f20f3181758385a1bb8c022d4041dfb4de84/skills/humanizer/SKILL.md), and [blader/humanizer](https://github.com/blader/humanizer/blob/1b48564898e999219882660237fde01bf4843a0f/SKILL.md)):

- **`HYPE-OPEN` — Hype openers and filler adjectives** (`delve`, `dive into`, `embark`, `unlock`, `elevate`, `seamlessly`, `robust`, `comprehensive`, `cutting-edge`, `powerful`, `leverage`, `harness`, `empower`, `streamline`, `effortless`, `tapestry`, `intricate`, `interplay`, `realm`, `pivotal`, `crucial`, `nuanced`, `dynamic`, `multifaceted`, `paradigm`, `synergy`, `holistic`, `unleash`, `foster`). Example: "This guide will help you unlock the full potential of..." → "This guide covers..."
- **`TRANS-BLOAT` — Transitional bloat** (`Moreover`, `Furthermore`, `In conclusion`, `In summary`, `It's worth noting`, `It's important to note`). Example: "Furthermore, the builder supports..." → "The builder supports..."
- **`PROMO` — Promotional flourish** (`world-class`, `best-in-class`, `next-generation`, `revolutionary`, `game-changing`, `state-of-the-art`, `seamless`, `unparalleled`, `unrivaled`, `premier`). Example: "a next-generation build system" → "a purpose-built build system"
- **`HEDGE` — Contextual hedging openers** (`In today's fast-paced world`, `In the ever-evolving landscape of`, `As we all know`, `It goes without saying`). Delete the opener and start with the actual statement.
- **`PRONOUN-OVERREACH` — Presumptuous collective pronouns** (`we've all been there`, `let's explore together`, `join me on this journey`). Use second person or neutral framing instead.
- **`RHETQ` — Rhetorical-question openers** (`Ever wondered…?`, `What if I told you…?`). State the topic directly.
- **`CANONICAL-LINT` — Canonical style anti-patterns** (`please`, `kindly`, `note that` as filler, ornamental parentheticals such as `(and this is important)`). Remove the filler; keep the statement.
- **`EM-DASH-DRAMA` — Em-dash as rhetorical pause** — em-dash used before a hype word or as a dramatic mid-sentence aside (e.g., `— unlocking`, `— making it`). Legitimate parenthetical em-dashes are fine.
- **`LEGACY-PUFF` — Significance or legacy claims** (`has left a lasting legacy`, `has had a profound impact on`, `stands as a testament to`, `remains a cornerstone of`). Replace with a specific, verifiable statement or delete.
- **`NOTABILITY-PUFF` — Notability flex** (`widely regarded as`, `has gained recognition`, `experts agree`, `industry leaders have noted`) *(advisory)*. Cite a source or delete.
- **`ING-BLOAT` — Gerund-chain abstractions** — chains of -ing nouns as subject or object where a finite verb would be clearer. Example: "Configuring and deploying involves setting up..." → "To deploy, set up..."
- **`WEASEL` — Vague attributions** (`some say`, `many believe`, `it has been suggested`, `critics argue`). Name the source or rewrite as a factual claim.
- **`FUTURE-OUTLOOK` — "Challenges and Future Prospects" boilerplate** — section headings or closing paragraphs following the AI outline pattern (`Looking Ahead`, `Future Directions`, `The Road Ahead`). Replace with a specific heading or delete.
- **`COPULA-DODGE` — Copula avoidance** (`serves as`, `functions as`, `acts as`, `operates as`, `plays the role of` where "is" or a concrete verb suffices). Example: "serves as the single source of truth" → "is the single source of truth"
- **`NEG-PARALLEL` — Negative parallelisms** (`not just … but`, `not only … but also`, `more than just`). State what the subject does directly.
- **`RULE-OF-THREE` — Rule-of-three overuse** — exactly three adjectives or nouns grouped for rhetorical balance rather than precision *(advisory)*. Use the most precise term.
- **`SYN-CYCLE` — Synonym cycling** — using different words for the same concept within a short span (e.g., "build manifest", "build descriptor", "build specification" for the same thing). Pick one term and use it throughout.
- **`FALSE-RANGE` — False ranges** (`from … to …` implying broad coverage from two arbitrary endpoints). List specific items instead.
- **`BOLD-OVERUSE` — Boldface overuse** — bold applied to adjectives, adverbs, or transitional words for decoration rather than to mark key terms or critical warnings.
- **`TITLE-CASE` — Title case in headings** — capitalising non-proper words in headings. Use sentence case; preserve proper nouns and acronyms.
- **`EMOJI` — Emojis** — any emoji outside a code fence. Delete; replace with a VitePress callout if semantic meaning is needed.
- **`CHATBOT-ARTIFACT` — Chatbot artifacts** (`Certainly!`, `Great question!`, `As I mentioned`, `I hope this helps`, `Feel free to ask`). Delete entirely.
- **`SYCOPHANT` — Sycophantic tone** (`great job`, `well done`, `excellent choice`, `congratulations on`). Delete; state the outcome directly.
- **`OVER-HEDGE` — Excessive hedging** — two or more hedges in one clause (`might possibly`, `could potentially`, `may perhaps`). Use at most one hedge where genuine uncertainty exists.
- **`GENERIC-CONCLUSION` — Generic positive conclusions** (`By following these steps`, `Armed with this knowledge`, `You are now ready to`, `You now have a solid understanding of`). Delete or replace with a concrete next step or link.

Filler words (`simply`, `just`, `easy`/`easily`, `actually`, `basically`, `obviously`) are a separate category governed by the style guide's banned-filler-word rule.

These categories describe concrete patterns to avoid at authoring time. The "no vague polish" refusal policy still applies for reviewers: contributors must identify a specific pattern from this list, not request general rewriting.

### Usability & Accessibility

Every person browsing documentation has different means and needs. They look for
different information and access documentation through different means. Language barriers or disabilities may present barriers when
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

Use this checklist when reviewing or submitting documentation:

### Core Markers

- ✅ All code and commands are tested and working
- ✅ Prerequisites are clearly stated
- ✅ Expected output is shown for verification steps
- ✅ Document has clear structure with descriptive headings
- ✅ One main idea per paragraph
- ✅ Sentences are concise and use active voice
- ✅ Neutral and professional language throughout
- ✅ Gender-neutral language used
- ✅ Consistent terminology (no synonym confusion)
- ✅ Project-specific abbreviations link to Glossary
- ✅ All images have descriptive alt text
- ✅ Links use descriptive text (not "click here")
- ✅ Proper heading hierarchy maintained
- ✅ Code examples have syntax highlighting
- ✅ Color is not the only indicator in visual media
- ✅ All links verified as working
- ✅ Document is discoverable via navigation/index
- ✅ Cross-referenced from related documentation
- ✅ Clear ownership indicated
- ✅ No AI-tell phrasing (see AI-generated phrasing to avoid: HYPE-OPEN, TRANS-BLOAT, PROMO, HEDGE, PRONOUN-OVERREACH, RHETQ, CANONICAL-LINT, EM-DASH-DRAMA, LEGACY-PUFF, ING-BLOAT, WEASEL, FUTURE-OUTLOOK, COPULA-DODGE, NEG-PARALLEL, SYN-CYCLE, FALSE-RANGE, BOLD-OVERUSE, TITLE-CASE, EMOJI, CHATBOT-ARTIFACT, SYCOPHANT, OVER-HEDGE, GENERIC-CONCLUSION)

### Conditional Markers

- ✅ Version compatibility noted (if applicable)
- ✅ Breaking changes highlighted (if applicable)
- ✅ Known issues section included (if applicable)
- ✅ External dependencies documented (if applicable)

## Architecture Decisions

- [ADR 0038: Public-by-Default Documentation Policy](/reference/adr/0038-public-by-default-documentation-policy)
  — the formal policy backing the single-source-of-truth and no-duplication maintainability markers.

## Related Topics

<RelatedTopics />
