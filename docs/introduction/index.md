---
title: "Introduction"
description: "How Garden Linux documentation is organized"
order: 1
github_org: gardenlinux
github_repo: docs
---

# Garden Linux

## Mission and Scope

The mission of the project is to develop a minimal, immutable, API-driven
operating system layer for automated, Kubernetes-centric platforms.

The scope of the Project includes collaborative development under the Project
Licenses, as defined in the project’s code repositories supporting the mission,
including documentation, testing, integration and the creation of other artifacts
that aid the development, deployment, operation or adoption of the open source
project.

It is **not** a general-purpose Operating System targeting all possible
use-cases & scenarios.

Instead, it is built to serve as:

- **Container runtime for [Gardener](/explanation/use-cases#gardener-kubernetes-nodes) or [vanilla Kubernetes](/explanation/use-cases#vanilla-kubernetes-nodes)** — The preferred Kubernetes worker node for 90% of the cloud applications deployed with Gardener
- **[Container base images](/explanation/use-cases#container-base-images)** — Our solution for packaging applications according
  to the OCI specification
- **[Virtualization host](/explanation/use-cases#virtualization-host)** — OS used to deploy hypervisor nodes to run Kubernetes nodes

## Documentation Overview

Garden Linux documentation uses the [Diátaxis framework](https://diataxis.fr/)
to organize content by what you need, not by your role. This page explains the
structure and helps you find the right section.

## Where to Start

| Your Situation                | Where to Go                                             |
| ----------------------------- | ------------------------------------------------------- |
| New to Garden Linux           | Start with [Tutorials](/tutorials/)                     |
| Use Cases                     | Get to know [Use Cases](/explanation/use-cases)         |
| Deploy on a specific platform | Go to [Platform-Specific Guides](/how-to/installation/) |
| Understand concepts           | Read [Explanation](/explanation/)                       |
| Look up specifications        | Search [Reference](/reference/)                         |
| Contribute to the project     | See [Contributing](/contributing/)                      |

## Tutorials

Learning-oriented guides that walk you through complete workflows. Tutorials
assume no prior experience, provide complete commands, and take 15--30 minutes
to complete.

**Start here**: [Tutorials](/tutorials/)

Tutorials cover local environments (Kernel-based Virtual Machine (KVM), Lima),
cloud platforms (Amazon Web Services (AWS), Microsoft Azure, Google Cloud
Platform (GCP), OpenStack), containers (Open Container Initiative (OCI) Image
Format), and bare-metal deployments.

## How-to Guides

Task-oriented directions for solving specific problems. These guides assume some
familiarity with Garden Linux and focus on practical solutions.

**Start here**: [How-to Guides](/how-to/)

Topics include [getting images](/how-to/getting-images),
[choosing flavors](/how-to/choosing-flavors),
[building images](/how-to/building-images),
[platform-specific deployment](/how-to/installation/).

## Explanation

Understanding-oriented articles that clarify concepts, provide background, and
explain how Garden Linux works.

**Start here**: [Explanation](/explanation/)

Topics include [use cases](/explanation/use-cases),
[Flavors](/explanation/flavors),
[architecture](/explanation/architecture),
[security posture](/explanation/security-posture), and
[design decisions](/explanation/architectural-decisions).

## Reference

Information-oriented technical descriptions, specifications, and lookup tables
for precise technical details.

**Start here**: [Reference](/reference/)

Includes the [flavor matrix](/reference/flavor-matrix),
[glossary](/reference/glossary), [kernel flavors](/reference/kernel-flavors),
[release information](/reference/releases/), Architecture Decision Records
(ADRs) in the [ADR catalog](/reference/adr/), and
[supporting tools documentation](/reference/supporting_tools/) (builder, Python
Garden Linux library).

## Contributing

Guidelines for contributing to Garden Linux, whether you are fixing a bug,
adding a feature, or improving documentation.

**Start here**: [Contributing](/contributing/)

Covers the documentation guide, development [workflow](/contributing/workflow),
[security](/contributing/security) practices, and
[testing](/contributing/testing) (developing tests, running tests, test
coverage).

## Getting Help

If you cannot find what you need:

1. Use the search feature in the top navigation
1. Check the [Troubleshooting](/how-to/troubleshooting/) guide
1. Visit the
   [Garden Linux GitHub repository](https://github.com/gardenlinux/gardenlinux)
1. Open an issue or discussion on GitHub
