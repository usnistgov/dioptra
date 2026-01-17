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

## Scenario 1: After a Minor or Major Release to Main

Use this workflow when a minor or major version has been released to `main` and you need to bump `dev` to stay one minor version ahead.

### Step 1: Run the bumpver command

For a minor release:

```sh
uvx tox run -e bumpver -- update -m -t dev
```

For a major release:

```sh
uvx tox run -e bumpver -- update --major -t dev
```

This command:

- Increments the minor version (`-m`) or major version (`--major`)
- Resets the dev tag to zero (`-t dev`)
- Updates version strings in all configured files
- Creates a release commit

### Step 2: Update uv.lock

The `uv.lock` file needs its version updated to match the new version.

> 📝 NOTE: Running `uv lock` by itself would update the `dioptra-platform` package version, but it also rewrites dependency markers throughout the file in ways that cause issues with this repository's optional dependency groups. This problem does not occur with `uv lock --upgrade`, which is used when upgrading dependencies. For version bumps where we only want to update the package version, we run `uv lock` to capture the correctly-formatted version string, then revert, then update only the appropriate line with the version change.

```sh
# Run uv lock to get the correctly-formatted version string
uv lock

# Capture the version from uv.lock before reverting
NEW_VERSION=$(sed -n '/^name = "dioptra-platform"$/{ n; s/^version = "\(.*\)"$/\1/p; }' uv.lock)

# Revert all changes to uv.lock
git checkout -- uv.lock

# Apply only the version change
sed -i '' '/^name = "dioptra-platform"$/{ n; s/^version = ".*"$/version = "'"$NEW_VERSION"'"/; }' uv.lock
```

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
git diff HEAD~1 uv.lock
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

Follow the same process as Scenario 1:

```sh
# Run uv lock to get the correctly-formatted version string
uv lock

# Capture the version from uv.lock before reverting
NEW_VERSION=$(sed -n '/^name = "dioptra-platform"$/{ n; s/^version = "\(.*\)"$/\1/p; }' uv.lock)

# Revert all changes to uv.lock
git checkout -- uv.lock

# Apply only the version change
sed -i '' '/^name = "dioptra-platform"$/{ n; s/^version = ".*"$/version = "'"$NEW_VERSION"'"/; }' uv.lock
```

### Step 3: Amend the release commit

```sh
git add uv.lock
git commit --amend --no-edit
```

### Step 4: Verify the result

```sh
uvx tox run -e bumpver -- show
git diff HEAD~1 uv.lock
```

## After Bumping the Version

Once the version bump is complete and verified:

1. Push the release commit to the remote `dev` branch
2. Create a git tag for the new version to trigger the release process

The tag creation will trigger automated builds for [PyPI](https://pypi.org/project/dioptra-platform) and the [container images](https://github.com/orgs/usnistgov/packages?repo_name=dioptra).
