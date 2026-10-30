# How to Bump the Dev Branch Version

Use this guide to advance the target version on `dev` after a stable release or to increment the counter for a development snapshot. Advancing the target version on `dev` does not by itself require publishing a snapshot. See [About Versioned Releases](about-versioned-releases.md#branch-life-cycles) for background and the [release policy](release-and-maintenance-policy.md#development-versions) for snapshot rules.

-   [Prerequisites](#prerequisites)
-   [Scenario 1: Advance the Development Target](#scenario-1-after-a-minor-or-major-release-to-main)
    -   [Step 1: Run bumpver](#step-1-run-the-bumpver-command)
    -   [Step 2: Update uv.lock](#step-2-update-uvlock)
    -   [Step 3: Amend the release commit](#step-3-amend-the-release-commit)
    -   [Step 4: Verify the result](#step-4-verify-the-result)
-   [Scenario 2: Increment the Development Snapshot Counter](#scenario-2-incrementing-the-dev-tag)
    -   [Step 1: Run bumpver](#step-1-run-the-bumpver-command-1)
    -   [Step 2: Update uv.lock](#step-2-update-uvlock-1)
    -   [Step 3: Amend the release commit](#step-3-amend-the-release-commit-1)
    -   [Step 4: Verify the result](#step-4-verify-the-result-1)
-   [README Installation Image Tags](#readme-installation-image-tags)
-   [After Bumping the Version](#after-bumping-the-version)

## Prerequisites

-   A clean working tree with `dev` checked out and up to date with `origin/dev`
-   [uv](https://docs.astral.sh/uv/) and `sed` installed, with tox available through `uv tool install --python 3.11 tox --with tox-uv`

Run the commands from the clone root. Bumpver displays development versions with a hyphen (`1.3.0-dev`), whereas `pyproject.toml` and Git tags use `1.3.0dev0` and `uv.lock` uses `1.3.0.dev0` (see [Version spellings](release-workflow-reference.md#version-spellings)). Bumpver commits its file changes locally without creating a Git tag or pushing.

<a id="scenario-1-after-a-minor-or-major-release-to-main"></a>

## Scenario 1: Advance the Development Target

Use this workflow after a minor or major release on `main` to advance `dev` to the next minor target.

<a id="step-1-run-the-bumpver-command"></a>

### Step 1: Run bumpver

Check the current version on `dev` with `uvx tox run -e bumpver -- show`. If `dev` still targets the version just released on `main`, increment the minor version and reset the `dev` counter:

```sh
uvx tox run -e bumpver -- update -m -t dev
```

For example, `1.2.0-dev` becomes `1.3.0-dev`, and `2.0.0-dev3` becomes `2.1.0-dev`. To set a specific target version directly (such as after a major release or when targeting `2.0.0-dev`), pass `--set-version`:

```sh
uvx tox run -e bumpver -- update --set-version 2.1.0-dev
```

<a id="step-2-update-uvlock"></a>

### Step 2: Update uv.lock

Update only the local `dioptra-platform` version entry in `uv.lock` to the PEP 440 normalized version (`X.Y.Z.devN`), without re-resolving other dependencies:

```sh
NEW_VERSION=$(sed -n 's/^version = "\(.*\)dev\([0-9]*\)"$/\1.dev\2/p' pyproject.toml | head -n 1)
sed -i.bak '/^name = "dioptra-platform"$/{ n; s/^version = ".*"$/version = "'"$NEW_VERSION"'"/; }' uv.lock
rm uv.lock.bak
uv lock --check
```

<a id="step-3-amend-the-release-commit"></a>

### Step 3: Amend the release commit

If a new stable release was just published on `main`, also update the [README installation image tags](#readme-installation-image-tags) now. Stage `uv.lock` (and `README.md` if updated) and amend the bumpver commit:

```sh
git add README.md uv.lock
git commit --amend --no-edit
```

<a id="step-4-verify-the-result"></a>

### Step 4: Verify the result

Verify the updated version and confirm that only the expected lines changed in `uv.lock` and `README.md`:

```sh
uvx tox run -e bumpver -- show
git diff HEAD~1 -- uv.lock README.md
```

<a id="scenario-2-incrementing-the-dev-tag"></a>

## Scenario 2: Increment the Development Snapshot Counter

Use this workflow when you want to publish a new development snapshot and the current `X.Y.ZdevN` version on `dev` has already been published.

First, check [How to Check Published Versions](how-to-check-published-versions.md). If the current version on `dev` (including `dev0`) has never been published, skip this scenario and tag the existing version directly with [How to Create a Release](how-to-create-a-release.md).

<a id="step-1-run-the-bumpver-command-1"></a>

### Step 1: Run bumpver

Increment the `dev` tag number (for example, `1.3.0-dev` to `1.3.0-dev1`, or `1.3.0-dev1` to `1.3.0-dev2`):

```sh
uvx tox run -e bumpver -- update --tag-num
```

<a id="step-2-update-uvlock-1"></a>

### Step 2: Update uv.lock

Update the local `dioptra-platform` entry in `uv.lock` and verify that the lockfile remains consistent:

```sh
NEW_VERSION=$(sed -n 's/^version = "\(.*\)dev\([0-9]*\)"$/\1.dev\2/p' pyproject.toml | head -n 1)
sed -i.bak '/^name = "dioptra-platform"$/{ n; s/^version = ".*"$/version = "'"$NEW_VERSION"'"/; }' uv.lock
rm uv.lock.bak
uv lock --check
```

<a id="step-3-amend-the-release-commit-1"></a>

### Step 3: Amend the release commit

Stage `uv.lock` (along with `README.md` if you also updated its stable image references) and amend the bumpver commit:

```sh
git add README.md uv.lock
git commit --amend --no-edit
```

<a id="step-4-verify-the-result-1"></a>

### Step 4: Verify the result

```sh
uvx tox run -e bumpver -- show
git diff HEAD~1 -- uv.lock README.md
```

## README Installation Image Tags

The `docker pull` commands in `README.md` reference the latest published stable release, even on `dev`. After publishing a stable release on `main`, update those tags on `dev`:

```sh
RELEASE_VERSION=1.2.1
sed -i.bak -E \
    's|^(docker pull ghcr[.]io/usnistgov/dioptra/[^:[:space:]]+:)[^[:space:]]+$|\1'"$RELEASE_VERSION"'|' \
    README.md
rm README.md.bak
```

Leave the deployment template `container_tag` on `dev` set to `dev` and keep `examples/examples-setup-requirements.txt` unbounded. If you are already running Scenario 1 or Scenario 2, include `README.md` in Step 3. Otherwise, commit `README.md` as an ordinary documentation change on `dev`:

```sh
git add README.md
git commit -m "docs: update stable installation image references"
```

<a id="after-bumping-the-version"></a>

## After Bumping the Version

Push the version commit to `origin/dev` (or open a pull request into `dev` if you do not push directly):

```sh
git push origin dev
```

If you are only advancing the target version after a stable release, stop here once `dev` CI passes.

If you are publishing a development snapshot, wait for CI checks to pass on the pushed commit, then follow [How to Create a Release](how-to-create-a-release.md) to tag that commit and publish to TestPyPI and GHCR.
