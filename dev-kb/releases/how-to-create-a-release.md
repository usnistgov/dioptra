# How to Create a Release

Use this guide to trigger a versioned release by creating and pushing an annotated Git tag. For background on Dioptra's versioning model, see [About Versioned Releases](about-versioned-releases.md). For details on the publishing workflows, see the [workflow and metadata reference](release-workflow-reference.md).

> [!NOTE]
> Tagging is currently performed manually after a release commit is adopted on `main` or `dev`, and the image workflow publishes version tags without `-buildN` suffixes or completed-build records. Update this guide when the tagging, numbered-build, and completed-build rows of the [implementation status](release-policy-implementation-status.md) apply now.

-   [Prerequisites](#prerequisites)
-   [Step 1: Verify Readiness](#step-1-verify-readiness)
-   [Step 2: Create and Push the Tag](#step-2-create-and-push-the-tag)
-   [Step 3: Monitor the Workflows](#step-3-monitor-the-workflows)
-   [Step 4: Verify Published Artifacts](#step-4-verify-published-artifacts)
    -   [Python Package](#python-package)
    -   [Docker Images](#docker-images)
-   [Troubleshooting](#troubleshooting)
    -   [Transient Failures](#workflow-failed-due-to-transient-issues)
    -   [Version Mismatches](#workflow-failed-due-to-version-mismatch)
    -   [Code or Configuration Failures](#workflow-failed-due-to-code-or-configuration-issues)
    -   [Partial Publication](#partial-failure-one-workflow-succeeded-one-failed)

## Prerequisites

-   Push access to the repository
-   A clean working tree
-   The release commit adopted on the target branch (`main` for a stable release, or `dev` for a development snapshot), with all branch CI checks passing on that commit
-   The target version confirmed unused via [How to Check Published Versions](how-to-check-published-versions.md)

To prepare a release commit first, follow [How to Merge Dev into Main](how-to-merge-dev-into-main.md) for a major or minor release, [How to Create a Patch Release](how-to-create-a-patch-release.md) for a patch release, or [How to Bump the Dev Branch Version](how-to-bump-dev-branch-version.md) for a development snapshot. Run the commands below from the clone root.

<a id="step-1-verify-readiness"></a>

## Step 1: Verify Readiness

Check out the target branch (`main` or `dev`), update it from `origin`, and confirm that `HEAD` is the intended release commit with the expected version in `pyproject.toml`:

```sh
TARGET_BRANCH=main  # or: dev
git checkout "$TARGET_BRANCH"
git pull --ff-only origin "$TARGET_BRANCH"

git log -n 1 --oneline
grep -m1 '^version = ' pyproject.toml
```

Confirm that the version printed from `pyproject.toml` matches the tag you are about to create (`1.2.1` for a stable release, or `1.3.0dev0` for a development snapshot) and that CI checks have passed for that commit on GitHub. If a later maintenance commit has already landed on the target branch after your release commit, set `RELEASE_COMMIT` to the exact release commit hash instead of `HEAD`.

<a id="step-2-create-and-push-the-tag"></a>

## Step 2: Create and Push the Tag

Create an annotated tag matching the `pyproject.toml` version string (without a `v` prefix) and push it to `origin`:

```sh
RELEASE_VERSION=1.2.1
RELEASE_COMMIT=HEAD

git tag -a "$RELEASE_VERSION" "$RELEASE_COMMIT" -m "Release $RELEASE_VERSION"
git push origin "refs/tags/$RELEASE_VERSION"
```

<a id="step-3-monitor-the-workflows"></a>

## Step 3: Monitor the Workflows

Pushing the version tag triggers two publishing workflows along with the standard test and documentation workflows:

1.  **Publish dioptra-platform package to PyPI** (`release.yml`)
2.  **Docker images** (`docker-images.yml`)

Open the [Actions tab](https://github.com/usnistgov/dioptra/actions) in the GitHub repository, select the runs triggered by the pushed tag, and monitor both workflows until all jobs complete.

<a id="step-4-verify-published-artifacts"></a>

## Step 4: Verify Published Artifacts

Once the workflows succeed, verify that both the Python distributions and the container images are available:

### Python Package

-   **Stable releases:** Confirm that the wheel (`.whl`) and source archive (`.tar.gz`) appear on [PyPI](https://pypi.org/project/dioptra-platform/).
-   **Development releases:** Confirm that the wheel and source archive appear on [TestPyPI](https://test.pypi.org/project/dioptra-platform/). Note that TestPyPI normalizes development versions (`1.3.0dev0` appears as `1.3.0.dev0`; see [Version spellings](release-workflow-reference.md#version-spellings)).

### Docker Images

Check [GitHub Packages](https://github.com/orgs/usnistgov/packages?repo_name=dioptra) and confirm that the release tag is present across all seven service images (`nginx`, `mlflow-tracking`, `restapi`, `pytorch-cpu`, `tensorflow2-cpu`, `pytorch-gpu`, and `tensorflow2-gpu`) with the expected architectures listed in [Service images and platforms](release-workflow-reference.md#service-images-and-platforms).

Because `docker-images.yml` pushes images to GHCR before signing them, also confirm that the signing, Rekor transparency log, and verification jobs in `docker-images.yml` succeeded. Optionally, test pulling an image:

```sh
docker pull ghcr.io/usnistgov/dioptra/restapi:<version>
```

## Troubleshooting

<a id="workflow-failed-due-to-transient-issues"></a>

### Transient Failures

If a workflow job fails because of a temporary network error or external registry outage:

1.  Open the failed workflow run in the GitHub Actions UI.
2.  Click **Re-run failed jobs**.
3.  Monitor the re-run to completion.

<a id="workflow-failed-due-to-version-mismatch"></a>

### Version Mismatches

If `release.yml` fails with a version mismatch error:

```text
Tag '1.2.0' does not match pyproject.toml version '1.2.1'
```

Because `docker-images.yml` runs independently and does not validate `pyproject.toml`, check whether `docker-images.yml` has already published images under the pushed tag:

-   **If either workflow published artifacts**, keep the tag and prepare a new release version for any correction.
-   **If neither workflow published artifacts** (for example, `docker-images.yml` was cancelled before pushing), delete the local and remote tag and create the correct tag:

    ```sh
    git tag -d <incorrect-tag>
    git push origin --delete <incorrect-tag>
    ```

<a id="workflow-failed-due-to-code-or-configuration-issues"></a>

### Code or Configuration Failures

If a build fails due to a bug in application code or `pyproject.toml` dependencies, do not move or reuse the existing tag. Prepare a new patch release (on `main`) or increment the `dev` snapshot counter (on `dev`) and release the fix under the new version number.

If a workflow fails because of the CI workflow or Docker build configuration, and the fix does not change application code or `pyproject.toml` requirements, do not release a new package version or create a `.postN` Git tag. Work out the recovery with the workflow maintainer.

<a id="partial-failure-one-workflow-succeeded-one-failed"></a>

### Partial Publication

Because `release.yml` and `docker-images.yml` run independently, one can succeed while the other fails. Keep the artifacts that succeeded, do not delete or move the release tag, and re-run the failed workflow if the error was transient. If recovery requires changing application code or `pyproject.toml` requirements, prepare a new release version as described in the [recovery policy](release-and-maintenance-policy.md#ownership-and-recovery). If it requires changing only workflow or build configuration, follow [Code or Configuration Failures](#workflow-failed-due-to-code-or-configuration-issues).
