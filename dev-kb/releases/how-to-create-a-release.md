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
- The release commit has been merged to the target branch (`main` or `dev`)
- The version in `pyproject.toml` has been bumped to the desired release version
- All CI checks have passed on the release commit

For instructions on bumping the version on the `dev` branch, see [How to Bump the Dev Branch Version](how-to-bump-dev-branch-version.md).

## Step 1: Verify Readiness

Confirm that the branch is ready for release:

```sh
# Fetch the latest changes
git fetch origin

# Check out the target branch
git checkout main  # or: git checkout dev

# Ensure your local branch matches the remote
git pull --ff-only

# Verify the version in pyproject.toml (first match is the package version)
grep -m1 '^version = ' pyproject.toml
```

The version shown should match the tag you're about to create. For example:

- For a stable release: `version = "1.2.0"`
- For a dev release: `version = "1.2.0dev0"`

## Step 2: Create and Push the Tag

Create an annotated tag matching the version in `pyproject.toml`:

```sh
# Create the tag
git tag -a <version> -m "Release <version>"

# Push the tag to trigger the release workflows
git push origin <version>
```

Replace `<version>` with your actual version string (e.g., `1.2.0` for stable releases, `1.2.0dev0` for dev releases). The tag format should match the version exactly, without a `v` prefix.

## Step 3: Monitor the Workflows

After pushing the tag, two GitHub Actions workflows will start:

1. **Publish dioptra-platform package to PyPI** (`release.yml`)
2. **Docker images** (`docker-images.yml`)

Monitor their progress:

1. Go to the [Actions tab](https://github.com/usnistgov/dioptra/actions) in the GitHub repository
2. Look for workflow runs triggered by the tag you just pushed
3. Click into each workflow to monitor individual job progress

The PyPI workflow typically completes faster than the Docker images workflow, which builds multiple images across multiple architectures.

## Step 4: Verify Published Artifacts

Once the workflows complete successfully, verify the artifacts were published:

### Python Package

For stable releases, verify the new version appears on the [PyPI project page](https://pypi.org/project/dioptra-platform/).

For prereleases (dev, rc, alpha, beta), verify the new version appears on the [TestPyPI project page](https://test.pypi.org/project/dioptra-platform/).

### Docker Images

Check [GitHub Packages](https://github.com/orgs/usnistgov/packages?repo_name=dioptra) for the published images. Each image should have tags corresponding to the release version.

You can also verify images are pullable:

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

The tag doesn't match the version in `pyproject.toml`. You'll need to:

1. Delete the incorrect tag:

   ```sh
   git tag -d <incorrect-tag>
   git push origin --delete <incorrect-tag>
   ```

2. Either fix the version in `pyproject.toml` or create the tag with the correct version

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
