---
name: humanizer
description: >
  Rework AI-generated phrasing in Garden Linux documentation. Use for "humanize
  this doc", "rework AI phrasing", "remove AI tells", "this reads like it was
  written by an LLM", or when editing Markdown under docs/ that shows chatbot or
  hype patterns. Provides the full pattern catalog and a minimal-rewrite workflow.
---

# Humanizer

Rework prose that carries AI-generated writing patterns into clear, direct
documentation. The goal is to remove recognizable LLM phrasing without changing
technical meaning.

This skill is the single source of truth for the AI-phrasing pattern catalog.
The documentation quality guide
(`docs/contributing/documentation/writing_good_docs.md`) summarizes the categories
and links here for the full list and rework guidance.

## Workflow

1. Scan the prose (ignore fenced code blocks and front matter).
2. For each suspect sentence, identify a **specific pattern ID** from the catalog
   below. If no pattern applies, leave the text unchanged.
3. Rewrite with the smallest possible edit that removes the pattern.
4. Preserve technical meaning. Do not add new claims, numbers, or sources.
5. Keep the result consistent with the project style guide (active voice, concise
   sentences, consistent terminology).

Refuse vague polish: never rewrite "to make it flow better". Every edit must cite
a pattern ID. Reviewers apply the same rule.

## Pattern catalog

Each entry gives the rule ID, the trigger, and a before to after example.

- **`HYPE-OPEN` - Hype openers and filler adjectives** (`delve`, `dive into`,
  `embark`, `unlock`, `elevate`, `seamlessly`, `robust`, `comprehensive`,
  `cutting-edge`, `powerful`, `leverage`, `harness`, `empower`, `streamline`,
  `effortless`, `tapestry`, `intricate`, `interplay`, `realm`, `pivotal`,
  `crucial`, `nuanced`, `dynamic`, `multifaceted`, `paradigm`, `synergy`,
  `holistic`, `unleash`, `foster`). Example: "This guide will help you unlock the
  full potential of..." to "This guide covers..."
- **`TRANS-BLOAT` - Transitional bloat** (`Moreover`, `Furthermore`,
  `In conclusion`, `In summary`, `It's worth noting`, `It's important to note`).
  Example: "Furthermore, the builder supports..." to "The builder supports..."
- **`PROMO` - Promotional flourish** (`world-class`, `best-in-class`,
  `next-generation`, `revolutionary`, `game-changing`, `state-of-the-art`,
  `seamless`, `unparalleled`, `unrivaled`, `premier`). Example: "a
  next-generation build system" to "a purpose-built build system"
- **`HEDGE` - Contextual hedging openers** (`In today's fast-paced world`,
  `In the ever-evolving landscape of`, `As we all know`, `It goes without
  saying`). Delete the opener and start with the actual statement.
- **`PRONOUN-OVERREACH` - Presumptuous collective pronouns** (`we've all been
  there`, `let's explore together`, `join me on this journey`). Use second person
  or neutral framing instead.
- **`RHETQ` - Rhetorical-question openers** (`Ever wondered...?`, `What if I told
  you...?`). State the topic directly.
- **`CANONICAL-LINT` - Canonical style anti-patterns** (`please`, `kindly`,
  `note that` as filler, ornamental parentheticals such as `(and this is
  important)`). Remove the filler; keep the statement.
- **`EM-DASH-DRAMA` - Em-dash as rhetorical pause** - em-dash used before a hype
  word or as a dramatic mid-sentence aside (for example `- unlocking`, `- making
  it`). Legitimate parenthetical em-dashes are fine.
- **`LEGACY-PUFF` - Significance or legacy claims** (`has left a lasting legacy`,
  `has had a profound impact on`, `stands as a testament to`, `remains a
  cornerstone of`). Replace with a specific, verifiable statement or delete.
- **`NOTABILITY-PUFF` - Notability flex** (`widely regarded as`, `has gained
  recognition`, `experts agree`, `industry leaders have noted`) *(advisory)*.
  Cite a source or delete.
- **`ING-BLOAT` - Gerund-chain abstractions** - chains of -ing nouns as subject
  or object where a finite verb would be clearer. Example: "Configuring and
  deploying involves setting up..." to "To deploy, set up..."
- **`WEASEL` - Vague attributions** (`some say`, `many believe`, `it has been
  suggested`, `critics argue`). Name the source or rewrite as a factual claim.
- **`FUTURE-OUTLOOK` - "Challenges and Future Prospects" boilerplate** - section
  headings or closing paragraphs following the AI outline pattern (`Looking
  Ahead`, `Future Directions`, `The Road Ahead`). Replace with a specific heading
  or delete.
- **`COPULA-DODGE` - Copula avoidance** (`serves as`, `functions as`, `acts as`,
  `operates as`, `plays the role of` where "is" or a concrete verb suffices).
  Example: "serves as the single source of truth" to "is the single source of
  truth"
- **`NEG-PARALLEL` - Negative parallelisms** (`not just ... but`, `not only ...
  but also`, `more than just`). State what the subject does directly.
- **`RULE-OF-THREE` - Rule-of-three overuse** - exactly three adjectives or nouns
  grouped for rhetorical balance rather than precision *(advisory)*. Use the most
  precise term.
- **`SYN-CYCLE` - Synonym cycling** - using different words for the same concept
  within a short span (for example "build manifest", "build descriptor", "build
  specification" for the same thing). Pick one term and use it throughout.
- **`FALSE-RANGE` - False ranges** (`from ... to ...` implying broad coverage from
  two arbitrary endpoints). List specific items instead.
- **`BOLD-OVERUSE` - Boldface overuse** - bold applied to adjectives, adverbs, or
  transitional words for decoration rather than to mark key terms or critical
  warnings.
- **`EMOJI` - Emojis** - any emoji outside a code fence. Delete; replace with a
  VitePress callout if semantic meaning is needed. GLDQ also enforces this
  automatically via the `EMOJI` rule.
- **`CHATBOT-ARTIFACT` - Chatbot artifacts** (`Certainly!`, `Great question!`,
  `As I mentioned`, `I hope this helps`, `Feel free to ask`). Delete entirely.
- **`SYCOPHANT` - Sycophantic tone** (`great job`, `well done`, `excellent
  choice`, `congratulations on`). Delete; state the outcome directly.
- **`OVER-HEDGE` - Excessive hedging** - two or more hedges in one clause (`might
  possibly`, `could potentially`, `may perhaps`). Use at most one hedge where
  genuine uncertainty exists.
- **`GENERIC-CONCLUSION` - Generic positive conclusions** (`By following these
  steps`, `Armed with this knowledge`, `You are now ready to`, `You now have a
  solid understanding of`). Delete or replace with a concrete next step or link.

## Filler words

Filler words (`simply`, `just`, `easy`/`easily`, `actually`, `basically`,
`obviously`) are a separate category governed by the style guide's
banned-filler-word rule. Delete them unless they carry literal meaning.

## References

- [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)
- [softaworks/agent-toolkit humanizer skill](https://github.com/softaworks/agent-toolkit/blob/3027f20f3181758385a1bb8c022d4041dfb4de84/skills/humanizer/SKILL.md)
- [blader/humanizer](https://github.com/blader/humanizer/blob/1b48564898e999219882660237fde01bf4843a0f/SKILL.md)
