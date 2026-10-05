# How to Bump the Dev Branch Version

This guide provides step-by-step instructions for creating a version release on the `dev` branch. For background on when and why dev releases happen, see [About Versioned Releases](about-versioned-releases.md).

- [Prerequisites](#prerequisites)
- [Scenario 1: After a Minor or Major Release to Main](#scenario-1-after-a-minor-or-major-release-to-main)
  - [Step 1: Run the bumpver command](#step-1-run-the-bumpver-command)
  - [Step 2: Update uv.lock](#step-2-update-uvlock)
  - [Step 3: Amend the release commit](#step-3-amend-the-release-commit)
  - [Step 4: Verify the result](#step-4-verify-the-result)
- [Scenario 2: Incrementing the Dev Tag](#scenario-2-incrementing-the-dev-tag)
  - [Step 1: Run the bumpver command](#step-1-run-the-bumpver-command-1)
  - [Step 2: Update uv.lock](#step-2-update-uvlock-1)
  - [Step 3: Amend the release commit](#step-3-amend-the-release-commit-1)
  - [Step 4: Verify the result](#step-4-verify-the-result-1)
- [After Bumping the Version](#after-bumping-the-version)

## Prerequisites

Before bumping the version, ensure you have:

- A clean working tree (no uncommitted changes)
- The `dev` branch checked out and up to date with the remote
- [uv](https://docs.astral.sh/uv/) installed and available on your PATH
- `sed` installed and available on your PATH

Run the commands from the root of the Dioptra clone. Install tox with `uv tool install --python 3.11 tox --with tox-uv` if needed. Bumpver creates a local commit automatically; it does not create a tag or push changes.

## Scenario 1: After a Minor or Major Release to Main

Use this workflow when a minor or major version has been released to `main` and you need to bump `dev` to stay one minor version ahead.

### Step 1: Run the bumpver command

Check the current version with `uvx tox run -e bumpver -- show`. If dev still targets the major and minor version just released on main, increment its minor version:

```sh
uvx tox run -e bumpver -- update -m -t dev
```

This applies after either a minor or major release. For example, `1.2.0-dev` becomes `1.3.0-dev`, and `2.0.0-dev3` becomes `2.1.0-dev`. If dev targets a different version, select the intended next minor version explicitly:

```sh
# Example after main releases 2.0.0
uvx tox run -e bumpver -- update --set-version 2.1.0-dev
```

Confirm the target before running the command; do not bump again if dev already has the intended version.

The command updates the configured version files, resets the dev tag to zero, and creates a release commit.

### Step 2: Update uv.lock

The `uv.lock` file needs its version updated to match the new version.

> 📝 NOTE: `uv lock` can also rewrite dependency markers and other lockfile content. For a version-only release, capture the formatted local package version, revert the lockfile, and apply only that version change. Dependency upgrades are a separate task.

```sh
uv lock
NEW_VERSION=$(sed -n '/^name = "dioptra-platform"$/{ n; s/^version = "\(.*\)"$/\1/p; }' uv.lock)
printf '%s\n' "$NEW_VERSION"
```

Confirm the captured value is nonempty and matches the intended version. For example, `1.3.0dev0` is normalized to `1.3.0.dev0` in the lockfile. Then restore the lockfile:

```sh
git checkout -- uv.lock
```

Apply only the local package version change:

```sh
sed -i.bak '/^name = "dioptra-platform"$/{ n; s/^version = ".*"$/version = "'"$NEW_VERSION"'"/; }' uv.lock
rm uv.lock.bak
```

The backup suffix works with macOS and GNU sed. Remove the temporary backup after the edit.

### Step 3: Amend the release commit

Add the `uv.lock` change to the release commit:

```sh
git add uv.lock
git commit --amend --no-edit
```

### Step 4: Verify the result

Confirm the version was bumped correctly:

```sh
uvx tox run -e bumpver -- show
```

Check that `uv.lock` shows only the version change:

```sh
git diff HEAD~1 -- uv.lock
```

## Scenario 2: Incrementing the Dev Tag

Use this workflow when you need to increment the dev tag number without changing the minor or major version. This applies when:

- A patch release to `main` has corresponding cherry-picks on `dev`
- Substantial new content on `dev` warrants a new development release

### Step 1: Run the bumpver command

```sh
uvx tox run -e bumpver -- update --tag-num
```

This command:

- Increments only the dev tag number (e.g., `1.2.0dev1` → `1.2.0dev2`)
- Updates version strings in all configured files
- Creates a release commit

### Step 2: Update uv.lock

Follow [Step 2 of Scenario 1](#step-2-update-uvlock) to capture the normalized version, restore the lockfile, and change only the local package version.

### Step 3: Amend the release commit

```sh
git add uv.lock
git commit --amend --no-edit
```

### Step 4: Verify the result

```sh
uvx tox run -e bumpver -- show
git diff HEAD~1 -- uv.lock
```

## After Bumping the Version

Once the version bump is complete and verified:

1. Adopt the version commit on remote `dev` using the permitted branch workflow. Maintainers with direct push permission can use `git push origin dev`; otherwise, use a pull request.
2. Wait for the applicable dev branch CI checks to pass on that exact commit.
3. Follow [How to Create a Release](how-to-create-a-release.md) to create and push the annotated version tag.

The tag push triggers automated publishing to [TestPyPI](https://test.pypi.org/project/dioptra-platform) and [GitHub Container Registry](https://github.com/orgs/usnistgov/packages?repo_name=dioptra). Keep development deployment defaults at `dev` and the example platform requirement unbounded. Stable installation references in the README continue to follow the published main release.
