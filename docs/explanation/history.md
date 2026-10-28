---
title: "Project History"
description: "How and why Garden Linux was created — a timeline from 2018 to the present"
related_topics:
  - /explanation/use-cases.md
  - /explanation/os-releases.md
  - /explanation/semver.md
  - /explanation/release-hierarchy.md
  - /reference/releases/release-lifecycle.md
  - /explanation/architecture.md
  - /explanation/compliance.md
  - /explanation/secure-boot.md
order: 1
github_org: gardenlinux
github_repo: gardenlinux
github_source_path: docs/explanation/history.md
github_target_path: docs/explanation/history.md
---

# Project History

## Background

Garden Linux was created inside SAP to solve a specific problem: running Kubernetes at scale
on cloud infrastructure without the overhead of a general-purpose operating system. The
project grew out of SAP's internal platform engineering work and was designed from the start
to be minimal, immutable, and fully automated.

## Why Garden Linux Was Created

### The Container-First Requirement

By 2018, SAP was running large numbers of Kubernetes clusters across multiple cloud providers.
The standard Linux distributions available at the time were designed for interactive use and
general workloads, carrying packages, services, and attack surface that container-only nodes
did not need.

### Minimal and Immutable by Design

The team's answer was to build an operating system that contained only what Kubernetes and
container runtimes require. Everything extraneous — compilers, package managers visible at
runtime, interactive shells by default — was removed. The filesystem is read-only in
production images, eliminating a broad class of runtime tampering.

### Debian as the Foundation

Debian was chosen as the upstream base because of its predictable release cadence, strong
security update practice, and wide ecosystem of pre-built packages. Garden Linux is not a
Debian derivative in the end-user sense: it uses Debian's package archive to build images
but does not ship Debian's installer or default configuration.

### Cloud and Kubernetes Integration

Each supported cloud platform (AWS, Azure, GCP, OpenStack, VMware, Alibaba Cloud) has a
dedicated feature set that installs only the platform-specific agent and configuration
needed. This keeps images small and avoids generic fallback code paths that can introduce
latency or security issues.

### Gardener as the First Customer

[Gardener](https://gardener.cloud) — SAP's open-source Kubernetes-as-a-service project —
needed a worker node OS it could provision, update, and replace fully automatically. Garden
Linux was designed to satisfy that requirement. Nodes boot, register, run workloads, and are
replaced without any manual intervention.

## Timeline Table

| Date | Type | Event | First released in |
|---|---|---|---|
| Jun 2018 | External Event | **CoreOS announces Container Linux end-of-life** — CoreOS announces via the [coreos-user mailing list](https://groups.google.com/forum/#!msg/coreos-user/zgqkG88DS3U/PFP9yrKbAgAJ) that Container Linux will be replaced by Fedora CoreOS. | - |
| Feb 2020 | External Event | **CoreOS declares Container Linux EOL** — CoreOS announces via the [coreos-user mailing list](https://groups.google.com/forum/#!msg/coreos-user/xM9TOqpwoWc/b-ciVxtjAwAJ) that Container Linux will reach end of life on 26 May 2020. | - |
| Mar 2020 | External Event | **Google announces Container Linux EOL on GCP** — Google announces that all Container Linux versions on Compute Engine will be unsupported from 26 May 2020 and unavailable for new VM instances thereafter. | - |
| Mar 2020 | External Event | **AWS announces Bottlerocket** — AWS publishes [Bottlerocket](https://aws.amazon.com/bottlerocket/), a new open-source container host OS, as a Container Linux replacement. | - |
| Mar 2020 | Announcement | **Garden Linux announced** — the SAP Gardener team announces Garden Linux _internally_ as a strategic countermeasure to the Container Linux end-of-life. | - |
| Mar 2020 | Release | **Initial git commits** — Garden Linux repository git repository is created. The first platform features ([`aws`](/reference/features/aws), [`azure`](/reference/features/azure), [`gcp`](/reference/features/gcp), [`openstack`](/reference/features/openstack), [`vmware`](/reference/features/vmware), [`kvm`](/reference/features/kvm)) are present from day one, along with the [`gardener`](/reference/features/gardener) feature for Gardener managed kubernetes clusters. The project is licensed under the MIT License. | [27.0](/reference/releases/release-notes/archived/27-0) |
| Apr 2020 | Release | **Garden Linux open-sourced on GitHub** — the Garden Linux repository at [github.com/gardenlinux/gardenlinux](https://github.com/gardenlinux/gardenlinux) is publicly announced. The community is invited to generate and test Garden Linux in canary clusters. | - |
| Apr 2020 | External Event | **Microsoft announces Container Linux EOL on Azure** — Microsoft announces that existing Container Linux resources will stop receiving updates after 26 May 2020, with resources deleted by 1 September 2020. | - |
| Apr 2020 | Release | **Beta Release Decision** — Garden Linux 1.0 Indirect Beta Release for Public Cloud is formally decided. | - |
| May 2020 | Release | **First release candidates available** — release candidates for AWS and GCP are made available for canary testing; Red Hat and SUSE are informed about the project. | - |
| May 2020 | Release | **GA Release Decision** — Garden Linux 1.0 Indirect GA Release for Public Cloud is formally decided. | - |
| May 2020 | Release | **Garden Linux GA** — Garden Linux is declared generally available. | - |
| Jun 2020 | Release | **[Release 27.0](/reference/releases/release-notes/archived/27-0)** — the first public Garden Linux image build. Version numbers represent days since the project epoch (2020-03-31). | [27.0](/reference/releases/release-notes/archived/27-0) |
| Aug 2020 | Adoption | **Adoption milestone** — Garden Linux node consumption surpasses CoreOS Container Linux and Suse CHOST across publicly accessible SAP landscapes. | - |
| Oct 2020 | Release | **[Release 184.0](/reference/releases/release-notes/archived/184-0)** | [184.0](/reference/releases/release-notes/archived/184-0) |
| Apr 2021 | Release | **[Release 318.4](/reference/releases/release-notes/archived/318-4)** | [318.4](/reference/releases/release-notes/archived/318-4) |
| Nov 2021 | Release | **[Release 576.0](/reference/releases/release-notes/archived/576-0)** | [576.0](/reference/releases/release-notes/archived/576-0) |
| Mar 2022 | Feature | **arm64 (AArch64) support added** — Garden Linux gains support for the ARM64 architecture, enabling deployment on ARM-based cloud instances. | [934.0](/reference/releases/release-notes/archived/934-0) |
| Apr 2022 | Feature (Security) | **Secure Boot support added** — the [`_secureboot`](/reference/features/_secureboot) feature flag is introduced, enabling UEFI Secure Boot for Garden Linux images. | [934.1](/reference/releases/release-notes/archived/934-1) |
| May 2022 | Feature (Compliance) | **CIS Benchmark hardening feature added** — the [`cis`](/reference/features/cis) feature provides Center for Internet Security benchmark hardening for Kubernetes nodes. | [576.0](/reference/releases/release-notes/archived/576-0) |
| Sep 2022 | Feature | **OCI container base image output** — the [`_oci`](/reference/features/_oci) feature enables Garden Linux to be published as an OCI-compatible container image. | [934.3](/reference/releases/release-notes/archived/934-3) |
| Jun 2023 | Release | **[Release 934.0](/reference/releases/release-notes/archived/934-0)** | [934.0](/reference/releases/release-notes/archived/934-0) |
| Aug 2023 | Feature | **Lima VM image support** — the [`lima`](/reference/features/lima) feature is introduced, enabling Garden Linux to run as a local development VM on macOS and Linux via Lima. | [1312.0](/reference/releases/release-notes/archived/1312-0) |
| Nov 2023 | Release | **[Release 1312.0](/reference/releases/release-notes/archived/1312-0)** | [1312.0](/reference/releases/release-notes/archived/1312-0) |
| Mar 2024 | Release | **[Release 1443.0](/reference/releases/release-notes/archived/1443-0)** | [1443.0](/reference/releases/release-notes/archived/1443-0) |
| Mar 2024 | Feature (Compliance) | **First DISA STIG implementation** — the [`stig`](/reference/features/stig) feature is the first implementation of Defense Information Systems Agency (DISA) Security Technical Implementation Guide (STIG) hardening for regulated workloads. | [1443.1](/reference/releases/release-notes/archived/1443-1) |
| Mar 2024 | Feature | **Google Distributed Cloud Hosted support** — the [`gdch`](/reference/features/gdch) feature enables Garden Linux on Google Distributed Cloud Hosted (GDCH) infrastructure. | [1443.1](/reference/releases/release-notes/archived/1443-1) |
| Aug 2024 | Release | **[Release 1592.0](/reference/releases/release-notes/archived/1592-0)** | [1592.0](/reference/releases/release-notes/archived/1592-0) |
| Sep 2024 | Feature (Security) | **Trusted boot chain** — the [`_trustedboot`](/reference/features/_trustedboot), [`_tpm2`](/reference/features/_tpm2), and [`_ephemeral`](/reference/features/_ephemeral) features are introduced, providing a complete TPM2.0-backed encrypted and verified boot chain. | [1877.0](/reference/releases/release-notes/archived/1877-0) |
| Oct 2024 | Feature | **Unified Kernel Image support** — the [`_usi`](/reference/features/_usi) feature enables building Garden Linux as a Unified Kernel Image (UKI) with an embedded EROFS root disk. | [1877.0](/reference/releases/release-notes/archived/1877-0) |
| Mar 2025 | Adoption/Platform | **Cluster API bare-metal support** — the [`capi`](/reference/features/capi) feature enables Garden Linux deployment on IronCore bare-metal via Cluster API. | [1877.0](/reference/releases/release-notes/archived/1877-0) |
| May 2025 | Release | **[Release 1877.0](/reference/releases/release-notes/archived/1877-0)** | [1877.0](/reference/releases/release-notes/archived/1877-0) |
| May 2025 | Feature | **In-place updates** — USI images can be updated in place to a new version using [`gardenlinux-update`](/reference/features/_usi), with atomic switchover and automatic rollback. | [1877.0](/reference/releases/release-notes/archived/1877-0) |
| Oct 2025 | Feature (Compliance) | **Initial FIPS 140-3 support** — first steps to get the [`_fips`](/reference/features/_fips) feature certified — provides FIPS 140-3 validated cryptography, targeting US government and regulated workloads. | [2150.0.0](/reference/releases/release-notes/archived/2150-0-0) |
| Dec 2025 | Feature | **Hardware conformance testing** — the [`checkbox`](/reference/features/checkbox) feature integrates the Checkbox hardware test kit for platform qualification. | [2150.0.0](/reference/releases/release-notes/archived/2150-0-0) |
| Feb 2026 | Release | **[Release 2150.0.0](/reference/releases/release-notes/archived/2150-0-0)** — first release using the new semver-compliant three-segment versioning scheme (`MAJOR.MINOR.PATCH`), as documented in [ADR-0011](/reference/adr/0011-garden-linux-versioning). | [2150.0.0](/reference/releases/release-notes/archived/2150-0-0) |
| Apr 2026 | Feature (Compliance) | **DISA STIG CAT III (low severity) compliance** — the [`disaSTIGlow`](/reference/features/disaSTIGlow) feature extends STIG coverage to low-severity controls. | - |
| May 2026 | Feature | **Automated installation** — the [`_autoinstall`](/reference/features/_autoinstall) and [`_install`](/reference/features/_install) features enable fully automated disk-based deployment to bare-metal targets. | - |
| May 2026 | Feature (Compliance) | **DISA STIG CAT II (medium severity) compliance** — the [`disaSTIGmedium`](/reference/features/disaSTIGmedium) feature extends STIG coverage to medium-severity controls. | - |
| Aug 2026 | Licensing/Legal | **License changed to Apache 2.0** — the project re-licenses under the Apache License 2.0. | - |
| Aug 2026 | Feature | **Cross-version in-place updates** — in-place updates across minor and major versions are supported using [`gardenlinux-update`](/reference/features/_usi). | [1877.27](/reference/releases/release-notes/archived/1877-27) / [2150.13.0](/reference/releases/release-notes/archived/2150-13-0) |
| Oct 2026 | Feature (Compliance) | **FIPS 140-3 submission** — all crypto modules have been successfully submitted to NIST and are now in the review phase. | - |
