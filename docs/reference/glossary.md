---
title: "Glossary"
order: 1
---

# Glossary

This glossary provides definitions for Garden Linux-specific terminology. To contribute additional terms or improve existing definitions, visit our [contributing guide](../contributing/index.md).

**Jump to:** [A](#a) · [B](#b) · [C](#c) · [D](#d) · [E](#e) · [F](#f) · [G](#g) · [I](#i) · [K](#k) · [L](#l) · [M](#m) · [N](#n) · [O](#o) · [P](#p) · [R](#r) · [S](#s) · [T](#t) · [U](#u) · [V](#v)

---

## A

### ADR (Architecture Decision Record)

A document that captures an important architectural decision made about the Garden Linux system. ADRs provide context, rationale, and consequences of decisions. Garden Linux stores ADRs in the [reference/adr](./adr/index.md) section. See [ADR-0001](./adr/0001-record-architecture-decisions.md) for more background on why Garden Linux uses ADRs, and [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) by Michael Nygard for the original concept.

### AppArmor

A Linux Security Module (LSM) that provides mandatory access control (MAC) by confining programs to a limited set of resources using per-program profiles. Garden Linux uses AppArmor as its default LSM for platforms requiring Kubernetes compatibility (for example, nodes running the [`gardener`](/reference/features/gardener) or [`khost`](/reference/features/khost) features). Some compliance features such as [`cis`](/reference/features/cis) replace AppArmor with SELinux instead. See [**SELinux**](#selinux) for the alternative LSM.

### Architecture

The processor architecture for which a Garden Linux image is built. Supported architectures include `amd64` (x86-64) and `arm64` (ARM 64-bit). The architecture is the second component of a flavor, e.g., `kvm-python-amd64` is a flavor (see [**Flavor**](#flavor)). See [Architecture documentation](/explanation/architecture.md) for details on Garden Linux system design.

### Artifact Base Name

The **artifact base name** is the versioned flavor qualified with a short commit hash:

```
{cname}-{arch}-{version}-{short_commit}
```

Example: `aws-gardener_prod-amd64-1877.3-a1b2c3d4`. The artifact base name is the prefix of every output file produced by the builder under `.build/` and the key used for S3 artifact storage. It uniquely identifies a specific build run. See [ADR 0035](/reference/adr/0035-cname-flavor-artifact-naming) for the authoritative definition.

### AWS

Amazon Web Services. One of the major cloud platforms supported by Garden Linux. Garden Linux provides AWS-specific images through the [`aws`](/reference/features/aws) platform feature with cloud-init integration and AWS-specific kernel modules. See [AWS platform guide](/how-to/installation/cloud/aws.md) and [AWS first boot tutorial](../tutorials/cloud/first-boot-aws.md) for usage details.

### Azure

Microsoft Azure. A major cloud platform supported by Garden Linux through the [`azure`](/reference/features/azure) platform feature with platform-specific image configurations and optimizations. See [Azure platform guide](/how-to/installation/cloud/azure.md) and [Azure first boot tutorial](../tutorials/cloud/first-boot-azure.md) for usage details.

---

## B

### Bare Metal

A platform target for Garden Linux images designed to run directly on physical hardware without a hypervisor. The `baremetal` feature is of type `platform`. The `metal` feature (which is of type `element`) provides standard kernel modules and physical hardware components and is distinct from `baremetal`. See [On-Premises Installation](/how-to/installation/on-premises/) and [Bare Metal first boot tutorial](../tutorials/on-premises/first-boot-bare-metal.md) for usage details. For the platform/element distinction, see [**Platform**](#platform) and [**Element**](#element).

### Builder

The [gardenlinux/builder](https://github.com/gardenlinux/builder) component that creates customized Linux distributions. The builder is a separate project maintained by the Garden Linux team and is used to build Garden Linux images with specific Flavors. See [Building Images documentation](/how-to/building-images.md) for practical guidance, [ADR-0020](./adr/0020-enforce-single-platform-by-default-in-builder.md) for details on platform enforcement in the builder, and [ADR-0031](./adr/0031-builder-glci-interface.md) for the builder-GLCI interface design.

### Versioned Flavor

A **versioned flavor** is the flavor qualified with a version — the string passed to the `./build` script to invoke a build:

```
{cname}-{arch}-{version}
```

Example: `aws-gardener_prod-amd64-1877.3`. See [ADR 0035](/reference/adr/0035-cname-flavor-artifact-naming) for the authoritative definition.

Partial arguments are accepted. You can pass any subset of the full [naming hierarchy](/reference/flavors#canonical-names):
a bare cname (e.g. `aws-gardener_prod`), a flavor (cname + arch, e.g.
`aws-gardener_prod-amd64`), or a versioned flavor (flavor + version, e.g.
`aws-gardener_prod-amd64-1877.3`). Any missing component is resolved
automatically: architecture defaults to the host architecture, and version is
read from the `VERSION` file via `./get_version`.

---

## C

### CIS (Center for Internet Security)

A framework providing security configuration benchmarks. Garden Linux offers optional CIS compliance through the [`cis`](/reference/features/cis) feature and related sub-features ([`cisAudit`](/reference/features/cisAudit), [`cisModprobe`](/reference/features/cisModprobe), [`cisOS`](/reference/features/cisOS), [`cisPackages`](/reference/features/cisPackages), [`cisPartition`](/reference/features/cisPartition), [`cisSshd`](/reference/features/cisSshd), [`cisSysctl`](/reference/features/cisSysctl)). See [ADR-0017](./adr/0017-feature-cis-to-retain-shell-scripts.md) for details on the CIS feature implementation and [ADR-0029](./adr/0029-cis-selinux-permissive.md) regarding SELinux in permissive mode for CIS compliance.

### chost (Container Host)

The [`chost`](/reference/features/chost) element feature adjusts Garden Linux to support running container and Kubernetes workloads. It installs and configures `containerd` and related packages. The [`khost`](/reference/features/khost) (Kubernetes Host) feature extends `chost` with additional Kubernetes-specific configuration. See [**khost (Kubernetes Host)**](#khost-kubernetes-host) and [**containerd**](#containerd).

### Cloud Image

A Garden Linux image optimized for cloud platforms (AWS, Azure, GCP, etc.) with cloud-init support and platform-specific configurations.

### CNAME (Canonical Name)

The **cname** is the minimal, canonically-sorted encoding of the feature set — and only the feature set. Architecture, version, and commit are not part of the cname:

```
cname = {feature-encoding}
```

**Minimality:** The cname encodes only the [minimal feature set](#minimal-feature-set) — features that are not already pulled in transitively by another selected feature are omitted. For example, if the [`aws`](/reference/features/aws) platform feature already depends on `cloud` transitively, then `aws-gardener` is a valid cname but `aws-cloud-gardener` is not, because `cloud` is redundant and therefore not minimal. The same rule applies to any transitively-included feature: listing it explicitly in the cname is invalid.

Example: `aws-gardener_prod`. The `GARDENLINUX_CNAME` entry in `/etc/os-release` contains the cname. See [ADR 0035](/reference/adr/0035-cname-flavor-artifact-naming) for the authoritative definition and [**GARDENLINUX_CNAME**](#gardenlinux_cname) for the environment variable.

### Container Image

A Garden Linux image packaged for use with container runtimes. Available through GitHub Packages at `ghcr.io/gardenlinux/gardenlinux`.

### containerd

An industry-standard container runtime that manages the lifecycle of containers on a host. Garden Linux includes `containerd` in the [`chost`](/reference/features/chost), [`khost`](/reference/features/khost), and [`gardener`](/reference/features/gardener) element features. Individual Garden Linux releases of `containerd` are maintained in the [gardenlinux/package-containerd](https://github.com/gardenlinux/package-containerd) repository. See [**chost (Container Host)**](#chost-container-host) and [**khost (Kubernetes Host)**](#khost-kubernetes-host).

---

## D

### Debian

The upstream Linux distribution on which Garden Linux is based. Garden Linux is a Debian GNU/Linux derivative that provides customized, auditable images with a focus on cloud and security features.

### debootstrap

A tool that installs a Debian base system into a subdirectory of another, already installed system. The Garden Linux builder uses `debootstrap` to create the initial root filesystem for every image, bootstrapping the `minbase` variant as the foundation for the [`base`](/reference/features/base) feature layer.

### Dependabot

GitHub's automated dependency update tool. See [ADR-0003](./adr/0003-builder-updates-dependabot.md) (later reverted by [ADR-0018](./adr/0018-revert-0003-builder-updates-dependabot.md)) for the history of Dependabot usage in the builder project.

### Distribution

Refers to a Garden Linux release or version. See [ADR-0002](./adr/0002-dists-can-never-change-retroactively.md) which establishes that distributions can never change retroactively, ensuring stability and reproducibility.

### dracut

The initramfs infrastructure used by Garden Linux to generate the initial RAM filesystem. Garden Linux uses dracut-generated initramfs instead of initramfs-tools used by standard Debian.

---

## E

### Element

A feature of type `element` represents a functional component or capability added on top of a platform feature. Elements are composable — multiple elements may be present in a single build. Examples: `cis`, `fedramp`, `firewall`, `gardener`, `metal`, `server`. See [ADR 0034](/reference/adr/0034-feature-terminology) for the authoritative definition.

### Ephemeral

Refers to the [`_ephemeral`](/reference/features/_ephemeral) feature that configures Garden Linux for stateless operation where no persistent state is maintained between reboots.

---

## F

### Feature

A modular component that adds specific functionality to a Garden Linux image. Features are defined in the `features/` directory. Every feature has exactly one type — `platform`, `element`, or `flag` — declared in its `info.yaml`. Features prefixed with an underscore (`_`) are of type `flag` (e.g., [`_prod`](/reference/features/_prod), [`_fips`](/reference/features/_fips)); the `_` prefix marks the feature as a flag, not as "internal" or "private". Features without a prefix are either `platform` or `element` types (e.g., [`aws`](/reference/features/aws), [`gardener`](/reference/features/gardener)). See [ADR 0034](/reference/adr/0034-feature-terminology) for the authoritative type definitions, [Flavors documentation](/explanation/flavors.md) for an overview, and [ADR-0032](./adr/0032-static-feature-test-coverage-analysis.md) for details on feature test coverage analysis.

### Feature Set

The **feature set** of a build is the complete set of features present after dependency graph resolution — the transitive closure of all included features minus all excluded ones. The **minimal feature set** is the subset of the feature set whose members are not pulled in transitively by any other selected feature; the [cname](#cname-canonical-name) is derived from this minimal set. See [ADR 0034](/reference/adr/0034-feature-terminology) and [ADR 0035](/reference/adr/0035-cname-flavor-artifact-naming) for details.

### FedRAMP

Federal Risk and Authorization Management Program. Garden Linux provides an optional [`fedramp`](/reference/features/fedramp) feature for US federal compliance requirements.

### FIPS

Federal Information Processing Standards. The [`_fips`](/reference/features/_fips) feature enables FIPS 140-2/140-3 cryptographic module compliance in Garden Linux.

### Flag

A feature of type `flag` represents a lightweight modifier. Flags are identified by a leading underscore (`_`) in their name (e.g., `_prod`, `_fips`, `_trustedboot`). They are intended for minor behavioral changes that do not warrant a full element and should not include other features. See [ADR 0034](/reference/adr/0034-feature-terminology) for the authoritative definition.

### Flavor

A **flavor** is the cname qualified with a target architecture:

```
{cname}-{arch}
```

Example: `aws-gardener_prod-amd64`. The flavor identifies what is being built for which architecture, independent of any particular release version. It is the natural unit for entries in `flavors.yaml` and CI job naming. See [ADR 0035](/reference/adr/0035-cname-flavor-artifact-naming) for the authoritative definition, [Flavors documentation](/explanation/flavors.md), [Choosing Flavors guide](/how-to/choosing-flavors.md), and [Flavor Matrix reference](./flavor-matrix.md) for more details.

### Frankenstein

A **frankenstein image** is a build that contains more than one `platform` feature. This is not a supported configuration. The builder enforces the single-platform rule by default; use `--allow-frankenstein` to override. When multiple platform features are present, `GARDENLINUX_PLATFORM` is set to the literal string `frankenstein`. See [ADR 0034](/reference/adr/0034-feature-terminology) and [ADR-0020](./adr/0020-enforce-single-platform-by-default-in-builder.md).

---

## G

### Garden Linux

A Debian GNU/Linux derivative designed to provide small, auditable Linux images for cloud providers and bare-metal machines. Garden Linux is optimized for Gardener nodes and provides extensive customization through features. See [Architectural Decisions](/explanation/architectural-decisions.md), [Use Cases](/explanation/use-cases.md), and [Security Posture](/explanation/security-posture.md) for more information.

### Gardener

[Gardener](https://gardener.cloud/) is a Kubernetes-based platform for managing clusters across multiple cloud providers. Garden Linux is the recommended operating system for Gardener worker nodes through the [`gardener`](/reference/features/gardener) feature.

### GARDENLINUX_CNAME

The `GARDENLINUX_CNAME` key in `/etc/os-release`. It contains the [cname](#cname-canonical-name) — the feature encoding only, without architecture, version, or commit hash. Example: `aws-gardener_prod`. See [ADR 0035](/reference/adr/0035-cname-flavor-artifact-naming) for the authoritative definition.

### GARDENLINUX_PLATFORM

The `GARDENLINUX_PLATFORM` key in `/etc/os-release`. It contains the single authoritative platform identifier for the image (e.g., `aws`, `kvm`, `baremetal`). It is derived from the resolved feature set: if exactly one `platform` feature is present, `GARDENLINUX_PLATFORM` is set to that feature's name; if more than one platform feature is present (frankenstein build), it is set to the literal string `frankenstein`. It is the value to use for all platform-routing decisions. See [ADR 0034](/reference/adr/0034-feature-terminology) for the authoritative definition.

### GCP

Google Cloud Platform. A major cloud platform supported by Garden Linux through the [`gcp`](/reference/features/gcp) platform feature with platform-specific configurations. See [GCP platform guide](/how-to/installation/cloud/gcp.md) and [GCP first boot tutorial](../tutorials/cloud/first-boot-gcp.md) for usage details.

### GitHub Actions

GitHub's continuous integration and deployment platform. Garden Linux uses GitHub Actions for automated testing and building. See [ADR-0028](./adr/0028-pin-actions-to-sha.md) for the decision to pin GitHub Actions to specific SHA hashes for security and reproducibility.

### GLCI

Garden Linux Continuous Integration. The CI pipeline that runs Garden Linux build, test, and publish workflows on GitHub Actions. GLCI consumes build artifacts and metadata uploaded to Amazon S3 by the builder, then runs automated tests against those artifacts. After successful testing, GLCI registers a release entry in the [Garden Linux Release Database (GLRD)](#glrd-garden-linux-release-database) and publishes images to the GitHub Container Registry and cloud provider image galleries. See [ADR-0031](./adr/0031-builder-glci-interface.md) for the builder-GLCI interface design and the [GitHub Workflows explanation](/explanation/github-workflows) for a detailed pipeline overview.

### GLRD (Garden Linux Release Database)

The Garden Linux Release Database. A system that tracks Garden Linux releases and their associated metadata — including version, commit, S3 artifact locations, and image identifiers for cloud platforms. GLRD entries are created automatically by the GLCI publish pipeline: `nightly` entries are created from main-branch builds, and `minor` entries are created from release-branch builds. The build requirements workflow resolves the correct artifact version and commit ID by querying GLRD. The database is hosted in the [gardenlinux/glrd](https://github.com/gardenlinux/glrd) repository. See [**GLCI**](#glci) and the [GitHub Workflows explanation](/explanation/github-workflows).

### GLVD

Garden Linux Vulnerability Database. A system for tracking and managing security vulnerabilities in Garden Linux packages and images.

### Go Dependencies

Garden Linux uses Go for various tools and components. See [ADR-0004](./adr/0004-vendoring-go-dependencies.md) for the decision to vendor Go dependencies.

---

## I

### Immutable

Refers to the optional immutable image feature where the root filesystem is read-only to prevent modifications and ensure system integrity.

### initramfs

Initial RAM filesystem. Garden Linux uses dracut to generate the initramfs, which is loaded by the kernel during the boot process before mounting the root filesystem.

---

## K

### Kernel

Garden Linux runs the latest Long Term Support (LTS) kernel from the Linux kernel project, providing up-to-date hardware support and security patches.

### khost (Kubernetes Host)

The [`khost`](/reference/features/khost) element feature adjusts Garden Linux to support running vanilla (non-Gardener) Kubernetes workloads. It extends the [`chost`](/reference/features/chost) feature with `kubelet` configuration, `sysctl` tuning, and swap removal. See [**chost (Container Host)**](#chost-container-host).

### KVM

Kernel-based Virtual Machine. A Linux kernel module that provides hardware virtualization capabilities. The [`kvm`](/reference/features/kvm) platform feature is a common target for Garden Linux images used in virtualized environments.

---

## L

### Lima (Linux Machines)

A tool for running Linux virtual machines on macOS and Linux hosts. Garden Linux provides official Lima images that can be launched with `limactl`. See [ADR-0023](./adr/0023-lima-image-download.md) for details on Lima image download mechanisms and [ADR-0024](./adr/0024-promote-lima-image-to-official.md) for the decision to promote Lima images to official status. Also see [Lima documentation](https://lima-vm.io) for more details.

### LTS Kernel

Long Term Support kernel. Garden Linux uses LTS kernel versions that receive extended security updates and bug fixes from the Linux kernel maintainers.

---

## M

### Major Version

The first number in Garden Linux's semantic versioning scheme (e.g., the "2017" in "2017.0.0"). Major versions may include breaking changes or significant architectural shifts. See [ADR-0011](./adr/0011-garden-linux-versioning.md) for the complete versioning strategy.

### Metal

The [`metal`](/reference/features/metal) feature is of type `element`. It provides standard kernel modules and physical hardware components for use on top of a platform feature. It is distinct from `baremetal`, which is the `platform` feature for running Garden Linux directly on physical hardware. See [**Bare Metal**](#bare-metal) and [**Element**](#element).

### Minimal Feature Set

The **minimal feature set** is the subset of the resolved feature set whose members are not pulled in transitively by any other selected feature. The [cname](#cname-canonical-name) is derived from the minimal feature set. See [ADR 0035](/reference/adr/0035-cname-flavor-artifact-naming) for details.

### Minor Version

The second number in Garden Linux's semantic versioning scheme (e.g., the "0" in "2017.0.0"). Minor versions typically add features or improvements in a backwards-compatible manner. See [ADR-0011](./adr/0011-garden-linux-versioning.md) for details.

---

## N

### Nightly Release

Automated builds of Garden Linux that occur on a regular schedule from the latest development code. Nightly releases are tagged as `nightly` and do not include maintenance commitments or updates. They are intended for testing and feedback, not production use.

---

## O

### OCI (OCI Image Format)

OCI Image Format. A container image specification defined by the Open Container Initiative. Garden Linux provides OCI-formatted container images. See [First Boot as OCI image](../tutorials/container/first-boot-oci.md) and the [OCI platform guide](/how-to/installation/container/index.md) for usage details.

### OpenSSL

The cryptographic library used by Garden Linux. Garden Linux uses OpenSSL 3.5 by default.

### OpenStack

An open-source cloud computing platform. Garden Linux provides OpenStack-specific images through the [`openstack`](/reference/features/openstack) platform feature.

### OpenTofu

An open-source infrastructure-as-code tool (a community fork of Terraform) used by the Garden Linux test suite to provision cloud infrastructure for platform tests. When running cloud-based tests, the `tests-ng` framework calls OpenTofu to deploy the image under test to the target cloud provider and tears down the resources after the test run completes. See [**tests-ng**](#tests-ng) and [OpenTofu documentation](https://opentofu.org).

---

## P

### package-build

The [gardenlinux/package-build](https://github.com/gardenlinux/package-build) repository providing the tooling and scripts used to build Garden Linux custom packages. Individual packages are maintained in separate `package-*` repositories (for example, `package-containerd`, `package-openssh`), each of which uses the common tooling from `package-build` to produce APT-installable `.deb` artifacts. See [Garden Linux Packaging explanation](/explanation/packaging) and [**repo-debian-snapshot**](#repo-debian-snapshot) for the snapshot repository used as a build input.

### Patch Version

The third number in Garden Linux's semantic versioning scheme (e.g., the "0" in "2017.0.0"). Patch versions contain backwards-compatible bug fixes and security updates. See [ADR-0011](./adr/0011-garden-linux-versioning.md) for details.

### Platform

A feature of type `platform` represents the deployment target — the combination of hardware, firmware, and cloud or hypervisor environment the image is intended to run on. A well-formed build must contain exactly one platform feature. Examples: `aws`, `azure`, `baremetal`, `container`, `gcp`, `kvm`. The single authoritative platform identifier for a running image is available in `GARDENLINUX_PLATFORM` in `/etc/os-release`. See [ADR 0034](/reference/adr/0034-feature-terminology) for the authoritative definition, [ADR-0020](./adr/0020-enforce-single-platform-by-default-in-builder.md) for the single-platform enforcement rule, and [**GARDENLINUX_PLATFORM**](#gardenlinux_platform).

### Podman

A daemonless container engine for developing, managing, and running OCI containers. Garden Linux uses rootless Podman by default for building images, though other container engines can be used with the `--container-engine` flag.

### PR References

Pull Request references in commit messages. See [ADR-0014](./adr/0014-enforce-pr-references-in-commits.md) for the requirement to enforce PR references in commits.

### python-gardenlinux-lib

The [python-gardenlinux-lib](https://github.com/gardenlinux/python-gardenlinux-lib) repository containing Python libraries and utilities for working with Garden Linux. See [ADR-0030](./adr/0030-python-gardenlinux-lib.md) for the architectural decision to create this library.

---

## R

### Release

A stable, versioned distribution of Garden Linux following semantic versioning. Releases are published on [GitHub Releases](https://github.com/gardenlinux/gardenlinux/releases) and GitHub Packages. See [ADR-0011](./adr/0011-garden-linux-versioning.md) for the versioning strategy and [ADR-0015](./adr/0015-no-backports-from-stable.md) for the policy on backports from stable branches.

### repo-debian-snapshot

The [gardenlinux/repo-debian-snapshot](https://github.com/gardenlinux/repo-debian-snapshot) repository that creates and maintains timestamped snapshots of the Debian testing repository. These snapshots are used as the APT source for Garden Linux builds, ensuring reproducibility: every build references a fixed, immutable snapshot rather than a live Debian mirror. Snapshots are hosted on Amazon S3 and mirrored to the GitHub Container Registry. See [Repository Infrastructure explanation](/explanation/repo-infrastructure).

### Rootless Podman

Running Podman without requiring root privileges. Garden Linux builds use rootless Podman by default, enhancing security by avoiding privileged operations during the build process.

---

## S

### sapmachine

An OpenJDK release maintained and supported by SAP. Garden Linux provides `sapmachine` as the [`sapmachine`](/reference/features/sapmachine) element feature, which installs the SapMachine Java runtime. The feature depends on [`_curl`](/reference/features/_curl) for package retrieval. See [SapMachine project](https://sap.github.io/SapMachine/).

### Secure Boot

A security feature that ensures only trusted software can boot on a system by verifying digital signatures. Garden Linux supports Secure Boot through the [`_trustedboot`](/reference/features/_trustedboot) feature. See [ADR-0005](./adr/0005-secure-boot-keys-glci.md) for details on Secure Boot keys in GLCI, and the [Secure Boot documentation](/how-to/secure-boot.md) for usage details.

### SELinux

Security-Enhanced Linux. An optional security feature available through the [`_selinux`](/reference/features/_selinux) feature that provides mandatory access control (MAC) security mechanisms. See [ADR-0029](./adr/0029-cis-selinux-permissive.md) for the decision regarding SELinux in permissive mode for CIS compliance.

### Semver

Semantic Versioning. Garden Linux follows the semver specification (MAJOR.MINOR.PATCH) starting with version 2017.0.0. See [ADR-0011](./adr/0011-garden-linux-versioning.md) for the complete versioning strategy and [semver.org](https://semver.org/) for the specification.

### STIG

Security Technical Implementation Guide. Garden Linux provides optional STIG compliance through the [`stig`](/reference/features/stig) and [`stigDev`](/reference/features/stigDev) features, based on DISA (Defense Information Systems Agency) security standards.

### systemd

The system and service manager used by Garden Linux. Garden Linux is purely systemd-based, using systemd-networkd for networking, systemd for service management, and other systemd components. See [ADR-0019](./adr/0019-standardize-on-systemd-timers.md) for the decision to standardize on systemd timers, and [ADR-0027](./adr/0027-no-systemd-rc.md) regarding the removal of systemd-rc.

---

## T

### tests

The testing framework used by Garden Linux for system testing. See [ADR-0006](./adr/0006-new-test-framework-in-place-self-contained-test-execution.md) (new test framework), [ADR-0007](./adr/0007-non-invasive-read-only-testing.md) (non-invasive testing), [ADR-0008](./adr/0008-unified-and-declarative-test-logic.md) (unified test logic), [ADR-0010](./adr/0010-incremental-migration-and-coexistence-of-tests.md) (incremental migration), [ADR-0016](./adr/0016-minimal-host-dependencies-for-test-ng.md) (minimal host dependencies), [ADR-0021](./adr/0021-use-of-tiger-tool-in-tests-ng.md) (tiger tool usage), [ADR-0022](./adr/0022-test-ng-system-state-diffing.md) (system state diffing), and [ADR-0026](./adr/0026-test-ng-when-to-parsers.md) (when-to parsers) for details on the test-ng architecture and design decisions.

### TPM2

Trusted Platform Module 2.0. A hardware-based security feature that can be enabled with the [`_tpm2`](/reference/features/_tpm2) feature for secure key storage and system integrity verification.

### Trusted Boot

An extension to Secure Boot that provides additional system integrity verification throughout the boot process. Garden Linux supports Trusted Boot through the [`_trustedboot`](/reference/features/_trustedboot) feature.

---

## U

### Unit Tests

Automated tests that validate the correct functionality of a Garden Linux image after it's created. Unit tests verify that the image contains expected packages, configurations, and behaviors. See [ADR-0013](./adr/0013-discontinue-packages-musthave-tests.md) for the decision to discontinue certain package must-have tests, and [ADR-0025](./adr/0025-disable-debsums-tests.md) for the decision to disable debsums tests.

### UKI (Unified Kernel Image)

A single Executable and Linkable Format (ELF) binary that combines the Linux kernel, the initramfs, and kernel command-line parameters — and optionally additional resources such as firmware and device trees — into one bootable image. UKIs are signed as a unit, which enables end-to-end Secure Boot verification without separate per-component signatures. See the [UAPI Group UKI specification](https://uapi-group.org/specifications/specs/unified_kernel_image/) for the authoritative definition. See also [**USI (Unified System Image)**](#usi-unified-system-image) for Garden Linux's extension of this concept.

### USI (Unified System Image)

A boot approach where the Linux kernel, initramfs, and root filesystem are combined into a single [UKI (Unified Kernel Image)](#uki-unified-kernel-image) with an embedded EROFS root disk. The [`_usi`](/reference/features/_usi) flag feature enables this mode in Garden Linux. USI images boot without a separate root partition and include the [`_nocrypt`](/reference/features/_nocrypt) and [`_unsigned`](/reference/features/_unsigned) features by default; they are incompatible with the [`_legacy`](/reference/features/_legacy) feature.

---

## V

### Virtual Machine Image

A Garden Linux image formatted for use with hypervisors like KVM, VMware, or cloud platform virtualization systems.

### VMware

A virtualization platform supported by Garden Linux. Garden Linux provides VMware-specific images through the [`vmware`](/reference/features/vmware) platform feature, including support for OVA (Open Virtual Appliance) format.
