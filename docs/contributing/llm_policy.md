---
title: "LLM/AI Policy"
description: "Guidelines regarding the use of Large Language Models for Contributions."
order: 3
---

# LLM Policy

We recognize that today LLMs have become a widely accepted set of tools to support software developers
in their day-to-day work.

Our policy in regards to LLM generated contributions to Gardenlinux is now as follows:

Contributors are free to use whatever tools they wish to craft their contributions, **as long
as a human is responsible for both the initial creation of a contribution (the prompting) as well as reviewing
the output of their tool.**

The contributor will always be seen as the author of their contribution and are thereby always
responsible for the entirety of their contribution. Contributors must be sufficiently confident that the
contribution is compliant to all formal requirements and best practices to be able to contribute to
Gardenlinux; and that this contribution is inherently worth bringing into the project.

## Transparency Requirements

Contributors **must be transparent and label contributions that contain any amount of LLM-generated content.**

This label must be present in the commit message as a message footer and must specify the exact tool name and model version.

:::details Example
```
Author: YourName <your@mail.com>
Date:    Wed Jul 22 15:53:00 2026 +0200
    
    Feat: Some New Feature

    Signed-off-by: YourName <your@mail.com>
    Assisted-by: Mistral Small 4 (mistral-ai/mistral-small-4)
```

If multiple tools are used, multiple Assisted-by blocks are necessary.
:::

For issues, discussions or any other kind of community post, an alternative suitable label can be applied.

::: details Example

In issues, you can add a `[AI-assisted]` tag into an issue description.

In comments, posts or emails to a maintainer, please specify whether your findings were created with the help
of AI, and to which extent.

```
I used Mistral Small 4 (mistral-ai/mistral-small-4) to help answer this question.
```

:::

This transparency helps us understand the role of these tools.

this policy includes, buit is not limited to, these types of contributions:

- Code contributions in any form (including CI configuration, build scripts and tests)
- Design Proposals or Discussions
- Issues or Security Vulnerability Reports
- Comments and Feedback on PRs
- Documentation

## Enforcement

We reserve the right to reject or revert any contribution - in any form - which is found to violate this policy.
