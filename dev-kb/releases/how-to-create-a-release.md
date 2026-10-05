# How to Create a Release

This guide provides step-by-step instructions for triggering a versioned release by pushing a git tag. For background on versioning philosophy and when releases happen, see [About Versioned Releases](about-versioned-releases.md). For details on the publishing infrastructure, see [About Release Publishing](about-release-publishing.md).

- [Prerequisites](#prerequisites)
- [Step 1: Verify Readiness](#step-1-verify-readiness)
- [Step 2: Create and Push the Tag](#step-2-create-and-push-the-tag)
- [Step 3: Monitor the Workflows](#step-3-monitor-the-workflows)
- [Step 4: Verify Published Artifacts](#step-4-verify-published-artifacts)
   - [Python Package](#python-package)
   - [Docker Images](#docker-images)
- [Troubleshooting](#troubleshooting)
   - [Workflow Failed Due to Transient Issues](#workflow-failed-due-to-transient-issues)
   - [Workflow Failed Due to Version Mismatch](#workflow-failed-due-to-version-mismatch)
   - [Workflow Failed Due to Code or Configuration Issues](#workflow-failed-due-to-code-or-configuration-issues)
   - [Partial Failure (One Workflow Succeeded, One Failed)](#partial-failure-one-workflow-succeeded-one-failed)

## Prerequisites

Before creating a release, ensure:

- You have push access to the repository
- Your working tree is clean and the intended version tag does not already exist
- The release commit has been adopted on the target branch (`main` or `dev`)
- The version in `pyproject.toml` has been bumped to the desired release version
- All CI checks have passed on the release commit

For stable preparation, follow [How to Merge Dev into Main](how-to-merge-dev-into-main.md). For a development version, follow [How to Bump the Dev Branch Version](how-to-bump-dev-branch-version.md). Run the commands below from the root of the Dioptra clone.

## Step 1: Verify Readiness

Confirm that the branch is ready for release:

```sh
# Fetch the latest changes
git fetch origin

# Check out the target branch
TARGET_BRANCH=main  # or: dev
git checkout "$TARGET_BRANCH"

# Ensure your local branch matches the remote
git pull --ff-only origin "$TARGET_BRANCH"
git rev-parse HEAD "origin/$TARGET_BRANCH"

# Verify the version in pyproject.toml (first match is the package version)
grep -m1 '^version = ' pyproject.toml
```

The two commit IDs must match the intended release commit, and its CI checks must have passed. Stop if local and remote branches differ. The version shown should match the tag you're about to create. For example:

- For a stable release: `version = "1.2.0"`
- For a dev release: `version = "1.3.0dev0"`

## Step 2: Create and Push the Tag

Create an annotated tag matching the version in `pyproject.toml`:

```sh
# Create the tag
git tag -a <version> -m "Release <version>"

# Push the tag to trigger the release workflows
git push origin <version>
```

Replace `<version>` with your actual version string (e.g., `1.2.0` for stable releases, `1.3.0dev0` for dev releases). The tag format should match the version exactly, without a `v` prefix.

## Step 3: Monitor the Workflows

After pushing the tag, two GitHub Actions workflows publish the artifacts:

1. **Publish dioptra-platform package to PyPI** (`release.yml`)
2. **Docker images** (`docker-images.yml`)

Monitor their progress:

1. Go to the [Actions tab](https://github.com/usnistgov/dioptra/actions) in the GitHub repository
2. Find runs triggered by the tag you just pushed and confirm their commit IDs match the tagged commit
3. Click into each workflow to monitor individual job progress

Tox tests and Sphinx documentation also run on version tags. Wait for all applicable tag checks as well as both publishing workflows. If a filtered Actions or CLI query returns no runs, inspect the broader run list and confirm each run's tag, trigger, and commit before concluding a workflow is missing.

## Step 4: Verify Published Artifacts

Once the workflows complete successfully, verify the artifacts were published:

### Python Package

For stable releases, verify the new version appears on the [PyPI project page](https://pypi.org/project/dioptra-platform/).

For prereleases (dev, rc, alpha, beta), verify the new version appears on the [TestPyPI project page](https://test.pypi.org/project/dioptra-platform/).

Confirm both the wheel and source archive are available for the intended version. Development version spellings can differ: a tag and project version of `1.3.0dev0` corresponds to TestPyPI version `1.3.0.dev0`. See [Version Format Variations](about-versioned-releases.md#version-format-variations).

### Docker Images

Check [GitHub Packages](https://github.com/orgs/usnistgov/packages?repo_name=dioptra) for the published images. Verify the exact release tag is visible for all seven images: nginx, mlflow-tracking, restapi, pytorch-cpu, tensorflow2-cpu, pytorch-gpu, and tensorflow2-gpu. Check the architectures against [About Release Publishing](about-release-publishing.md#multi-architecture-builds).

GHCR tag visibility is sufficient for this check. Optionally, verify an image is pullable:

```sh
docker pull ghcr.io/usnistgov/dioptra/restapi:<version>
```

## Troubleshooting

### Workflow Failed Due to Transient Issues

If a workflow fails due to network issues or temporary unavailability of external services (base image registries, PyPI, etc.):

1. Go to the failed workflow run in the GitHub Actions UI
2. Click "Re-run failed jobs" to restart from the failure point
3. Monitor the re-run for success

### Workflow Failed Due to Version Mismatch

If the release workflow fails with a version mismatch error:

```text
Tag '1.2.0' does not match pyproject.toml version '1.2.1'
```

Check the tagged commit's version and the results of both publishing workflows before changing the tag. If either workflow has published artifacts, preserve that release history and use a new version for any correction.

If neither workflow has published artifacts, remove the incorrect tag after confirming its name and that it is safe to delete:

```sh
git tag -d <incorrect-tag>
git push origin --delete <incorrect-tag>
```

Return to the readiness check and create a tag matching the prepared commit. If the package version itself needs correcting, prepare and validate the corrected commit first.

### Workflow Failed Due to Code or Configuration Issues

If the failure is due to an issue in the repository itself:

**For issues in `src/dioptra/` (affects the package):**

1. Fix the issue in a new commit
2. Increment the patch version (for `main`) or dev tag (for `dev`)
3. Create a new release with the incremented version

**For configuration issues that don't affect the package:**

On the `dev` branch:

1. Fix the issue in a new commit
2. Increment the dev tag number (e.g., `1.2.0dev0` → `1.2.0dev1`)
3. Create a new release with the incremented dev tag

On the `main` branch:

1. Fix the issue in a new commit
2. Add a post-release version tag (e.g., `1.2.0.post1`)
3. Create a new release with the post version

### Partial Failure (One Workflow Succeeded, One Failed)

The PyPI and Docker workflows run independently. If one succeeds and the other fails:

- The successful artifacts are already published and valid
- Follow the troubleshooting steps above for the failed workflow
