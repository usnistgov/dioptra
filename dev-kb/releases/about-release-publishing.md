# About Release Publishing

This document explains the design decisions and infrastructure behind Dioptra's automated release publishing process. For background on versioning philosophy and when releases happen, see [About Versioned Releases](about-versioned-releases.md). For stable preparation, see [How to Merge Dev into Main](how-to-merge-dev-into-main.md). For step-by-step instructions on triggering a release, see [How to Create a Release](how-to-create-a-release.md).

- [Published Artifacts](#published-artifacts)
- [PyPI Publishing](#pypi-publishing)
  - [Trusted Publishers](#trusted-publishers)
  - [Prerelease Routing](#prerelease-routing)
- [Docker Image Publishing](#docker-image-publishing)
  - [Multi-Architecture Builds](#multi-architecture-builds)
  - [Image Signing](#image-signing)
- [Version Validation](#version-validation)
- [Workflow Triggers](#workflow-triggers)
- [Release Review and Main Adoption](#release-review-and-main-adoption)
- [Failure Scenarios](#failure-scenarios)

## Published Artifacts

A Dioptra release produces two categories of artifacts:

- **Python package**: The `dioptra-platform` package published to [PyPI](https://pypi.org/project/dioptra-platform) (stable releases) or [TestPyPI](https://test.pypi.org/project/dioptra-platform) (prereleases)
- **Docker images**: Container images for each Dioptra service, published to [GitHub Container Registry (GHCR)](https://github.com/orgs/usnistgov/packages?repo_name=dioptra)

These artifacts are produced by separate GitHub Actions workflows that both trigger on version tag pushes.

## PyPI Publishing

### Trusted Publishers

Dioptra uses PyPI's [trusted publisher](https://docs.pypi.org/trusted-publishers/) mechanism for authentication rather than API tokens. This approach:

- Eliminates the need to manage and rotate long-lived credentials
- Uses OpenID Connect (OIDC) to establish trust between GitHub Actions and PyPI
- Requires configuring the trusted publisher on PyPI with the GitHub repository and workflow filename

When the workflow runs, GitHub provides a short-lived OIDC token that PyPI validates against the trusted publisher configuration. If the token matches (correct repository, workflow, and environment), PyPI accepts the upload.

### Prerelease Routing

The publishing workflow automatically routes packages based on version type:

| Version Type | Example                                       | Destination       |
| ------------ | --------------------------------------------- | ----------------- |
| Stable       | `1.2.0`                                       | PyPI (production) |
| Prerelease   | `1.2.0dev0`, `1.2.0rc1`, `1.2.0a1`, `1.2.0b1` | TestPyPI          |

This routing is determined by inspecting the version string for prerelease indicators (`dev`, `rc`, `alpha`, `beta`, etc.). The separation allows testing the publishing pipeline and package installation without polluting the production index.

## Docker Image Publishing

### Multi-Architecture Builds

Dioptra builds Docker images for multiple CPU architectures:

| Image           | `linux/amd64` | `linux/arm64` |
| --------------- | :-----------: | :-----------: |
| nginx           |      Yes      |      Yes      |
| mlflow-tracking |      Yes      |      Yes      |
| restapi         |      Yes      |      Yes      |
| pytorch-cpu     |      Yes      |      Yes      |
| tensorflow2-cpu |      Yes      |      Yes      |
| pytorch-gpu     |      Yes      |      No       |
| tensorflow2-gpu |      Yes      |      No       |

The GPU worker images are currently configured to build for `amd64` only.

The build process:

1. Builds platform-specific images in parallel on appropriate runners
2. Pushes images by digest (content hash) to GHCR
3. Creates multi-architecture manifest lists that reference both platform variants
4. Tags the manifest with version identifiers

This approach allows users to pull images without specifying architecture. Docker automatically selects the appropriate variant for the host system.

### Image Signing

Docker images are cryptographically signed to satisfy compliance requirements. The signing process uses a FIPS-compliant approach:

1. **Payload generation**: `cosign generate` creates a JSON payload containing the image digest and metadata
2. **FIPS-compliant signing**: OpenSSL signs the payload using a private key in a FIPS-validated environment
3. **Signature attachment**: `cosign attach signature` associates the signature with the image in GHCR
4. **Transparency logging**: The signature is recorded in the [Rekor](https://docs.sigstore.dev/logging/overview/) transparency log, creating an immutable audit trail
5. **Verification**: Both the Rekor entry and the attached signature are verified before the workflow completes

A signing or verification failure causes the workflow to fail. Images are uploaded before signing, so registry visibility alone does not establish that signing and verification finished successfully.

## Version Validation

Before Python package publication, `release.yml` validates that the git tag matches the version declared in `pyproject.toml`. This validation:

- Prevents accidental mismatches between tag and package version
- Ensures the published package version matches what users expect from the tag
- Catches errors before the Python package is uploaded

The validation is performed by a reusable GitHub Action (`.github/actions/validate-release-tag/`) that:

1. Extracts the version from `pyproject.toml`
2. Compares it against the triggering tag
3. Determines if the version is a prerelease (for routing decisions)
4. Fails the workflow if there's a mismatch

The Docker workflow runs independently and does not use this package-version validation action. A package version mismatch can therefore coexist with published images.

Release tags use the project version without a `v` prefix. The validator currently permits stripping a leading `v`, but this does not change the naming convention; Docker version tags also use the raw Git tag.

## Workflow Triggers

Both publishing workflows trigger on git tags matching the pattern `*.*.*`:

- **`release.yml`**: Runs unit tests, validates the tag, builds the Python package, and publishes to PyPI/TestPyPI
- **`docker-images.yml`**: Builds, signs, and publishes Docker images to GHCR

The workflows run independently and in parallel. A single tag push triggers both workflows simultaneously.

The Docker images workflow also triggers on:

- **Pushes to `main` or `dev` branches**: Builds images tagged with the branch name
- **Pull requests to `main` or `dev`**: Builds images for validation (tagged with PR number)
- **Weekly schedule**: Rebuilds images to incorporate base image updates

Tox and Sphinx also run on version tag pushes. Branch pushes and PR checks validate release preparation but do not publish a Python package to PyPI or TestPyPI; tag publication is a separate step.

## Release Review and Main Adoption

Stable preparation creates one merge commit with current main as its first parent and the prepared dev changes as its second parent. The resolved commit is published on the release branch for PR review and CI while main remains unchanged. A release branch push runs Tox and Sphinx; a mergeable PR runs Docker images and Frontend Playwright e2e, plus Frontend checks when their path filters match. GitHub does not run `pull_request` workflows while merge conflicts remain.

PR workflows can check out a temporary test merge at `refs/pull/<number>/merge`. Its commit ID differs from the prepared release commit, but its tree should match when main has not changed. This temporary commit is CI input and does not become another merge in main's history.

After checks pass and the main base is rechecked, a maintainer with permission to update protected main directly fast-forwards it to the prepared commit and pushes normally. GitHub marks the PR merged because its head commit is now reachable from main. This method preserves one integration merge and differs from the ordinary squash workflow in `CONTRIBUTING.md`. Using a GitHub merge button would change the selected history. If main advances, the candidate and its checks must be revised before adoption.

Main pushes run branch CI, publish branch-tagged images, and deploy Sphinx documentation. Successful main checks precede the version tag and its publication workflows. See [How to Merge Dev into Main](how-to-merge-dev-into-main.md) for the commands.

## Failure Scenarios

Several conditions can cause publishing to fail:

| Scenario          | Cause                                                                     | Resolution                                               |
| ----------------- | ------------------------------------------------------------------------- | -------------------------------------------------------- |
| Version mismatch  | Git tag doesn't match `pyproject.toml` version                            | Fix the version, create a new tag                        |
| PyPI rejection    | Version already exists on PyPI                                            | Increment version, create a new release                  |
| Network issues    | Temporary connectivity problems with PyPI, GHCR, or base image registries | Restart the failed workflow from the GitHub Actions UI   |
| Build failure     | Code or configuration issue                                               | Fix the issue and create a new release (see below)       |
| Signature failure | Problems with signing keys or Rekor                                       | Investigate the specific error; may require key rotation |

When a build fails due to repository issues rather than transient problems:

- **Code issues under `src/dioptra/`**: Fix with a bug patch, increment the patch version (or dev tag), and create a new release
- **Configuration issues not affecting the package**: On `dev`, fix and increment the dev tag; on `main`, fix and add a post-release version tag

Because the PyPI and Docker workflows run independently, it's possible for one to succeed while the other fails. The Docker images are built from the repository's `uv.lock` file rather than installing the published wheel, so a Docker build failure doesn't affect the PyPI package and vice versa.
