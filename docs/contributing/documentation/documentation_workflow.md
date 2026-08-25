---
title: Documentation Workflow
description: How to Contribute Documentation to Garden Linux
order: 1
related_topics:
  - /contributing/documentation/writing_good_docs.md
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

# Documenting Garden Linux

This guide will provide you with a detailed overview over everything you need to
know to support our efforts in documenting the Garden Linux project.

If you would like to know what markers we use to determine if submitted
documentation is good, check our guide about
[Document Quality Markers](./writing_good_docs.md)

## When Is Documentation Necessary?

Documentation is always necessary when a piece of software, a process or
information is touched that has implications for other people. May they be
internal or external contributors, users or decision makers.

## What Should Be Documented?

In the context of this Documentation Hub, anything that has implication to the
"outside". Meaning other users, operators, developers or decision makers needs
to be documented accordingly (see [ADR 0038](/reference/adr/0038-public-by-default-documentation-policy) for the full policy).

This includes, but is not limited to:

- Usage of Garden Linux and any supporting tool
- Processes used to develop or maintain Garden Linux or any supporting tool
- Features and components of the project
- Ways to contribute and where to find help
- Information about where to submit security incidents
- Information about who is developing the project

Of course this does not apply to purely internal changes like code cleanup
contributions or similar that have no outside effect. For a precise definition
of what qualifies as internal, see [ADR 0038](/reference/adr/0038-public-by-default-documentation-policy).

## Who Is Responsible for Maintaining Documentation?

The question of _"who is responsible?"_ can be split into two roles: The
contributors and a documentation lead.

### Contributors

Contributors are defined as individuals, groups or organisations that submit
code or non-code contributions to the project. These should, in addition to
their submission, document their changes with appropriate changes to any
relevant pieces of documentation. This applies to _any contribution_ if the
change is relevant for others.

For example:

1. A person introduces a new feature to Garden Linux and opens a Pull Request
2. A maintainer reviews said feature and advises the contributor to write
   documentation for it
3. Said documentation will be reviewed by the maintainer in question or the
   documentation lead if applicable
4. If both the code and the documentation fulfill their respective
   [quality markers](./writing_good_docs.md), the PR is merged

### The Documentation Lead

This is a more or less informal position that is quite common in many projects:
One maintainer/developer who is responsible for handling the documentation hub
and enforcing [quality standards](./writing_good_docs.md).

This can be a liaison to a formal documentation team who is briefed on the
project and works closely with the development team, a team member that is
permanently appointed to or volunteers for this position, or a rotating position
that anyone in the team may take on for a set amount of time.

However this may be implemented, _**documentation is a team effort**_.

The responsibilities of this person are:

- Evaluating whether a contribution requires documentation & what scope that
  documentation needs to be
- Making sure that documentation is written and put in the correct place
- Ensuring that the documentation pipeline is running and the documentation
  website is accessible

### Documentation Ownership

Documentation ownership depends on the scope:

- **Subproject documentation** (e.g., builder, python-gardenlinux-lib): Owned
  and maintained by the contributors most active on that subproject if no formal
  assignment to said project exist
- **Documentation hub content** (e.g., these contributing guides): Owned by the
  Documentation Lead if that role exists, otherwise by the core team
  collectively

## How to Submit Documentation Changes

To contribute documentation to Garden Linux:

1. **Create a branch** named descriptively ideally with a `docs/` prefix
2. **Make your changes** following the [quality markers](./writing_good_docs.md)
3. **Add front-matter** to your markdown files according to the
   [technical reference](./technical.md)
4. **Test your changes** locally by running the documentation server Check the
   [documentation testing guide](./testing.md)
5. **Open a Pull Request** with:
   - Clear description of what documentation was added/changed
   - Reference to any related code changes or issues
   - Screenshots if visual changes were made
6. **Address review feedback** from maintainers or the Documentation Lead

## The Review Process

Any changes to documentation will be reviewed by maintainers for the criteria
listed in the [quality criteria guide](./writing_good_docs.md). Only after the
review is successful will the changes be merged.

In cases where there is a Documentation Lead, this person must review changes to
documentation for their adherence to the project's quality markers.

In cases where there is **no** dedicated Documentation Lead, documentation
changes must be reviewed by other team members and tweaked according to their
feedback until unanimous agreement is reached.

The review validates:

- **Technical accuracy and sufficient depth**: The document matches implemented
  behaviour, commands are correct and tested
- **Completeness**: All affected changes are documented, prerequisites are
  stated, next steps are provided
- **Readability**: The documentation is free of typos and grammatical errors,
  has clear structure and flows logically
- **Style and Inclusivity**: Language follows the project's
  [quality criteria](./writing_good_docs.md), all images have appropriate alt
  text descriptions
- **Maintainability**: Documentation follows the [single source of truth](/reference/adr/0038-public-by-default-documentation-policy) principle,
  ownership is clear, no unnecessary duplication

## Architecture Decisions

- [ADR 0038: Public-by-Default Documentation Policy](/reference/adr/0038-public-by-default-documentation-policy)
  — defines what must be public, what stays internal, and the delta-only model for internal supplements.

## Related Topics

<RelatedTopics />
