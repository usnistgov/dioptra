# How to Merge Dev into Main

This guide provides step-by-step instructions for bringing changes from `dev` into `main` for a stable release. For background on branch versions, see [About Versioned Releases](about-versioned-releases.md). Tagging and publication are covered in [How to Create a Release](how-to-create-a-release.md).

- [Prerequisites](#prerequisites)
- [Step 1: Create the Release Branch](#step-1-create-the-release-branch)
- [Step 2: Prepare the Stable Version](#step-2-prepare-the-stable-version)
- [Step 3: Merge with Main Locally](#step-3-merge-with-main-locally)
- [Step 4: Open the Release Pull Request](#step-4-open-the-release-pull-request)
- [Step 5: Wait for the Checks](#step-5-wait-for-the-checks)
- [Step 6: Update Main](#step-6-update-main)
- [After Merging](#after-merging)

## Prerequisites

Before preparing the release, ensure you have:

- A clean Dioptra clone and an up-to-date `dev` branch containing the agreed release changes
- [uv](https://docs.astral.sh/uv/) installed, with tox available through `uv tool install --python 3.11 tox --with tox-uv`
- The agreed stable version number
- Permission to push a release branch and update protected `main` directly

Run the commands from the clone root in the same shell. The examples use `1.2.0`; substitute the version you are preparing. This procedure creates one local merge commit, then fast-forwards main after PR checks. Do not use GitHub's merge, squash, or rebase buttons for this release.

## Step 1: Create the Release Branch

Fetch the current branches, update dev, and create the release branch:

```sh
git fetch origin
git checkout dev
git pull --ff-only origin dev

RELEASE_VERSION=1.2.0
MAIN_BASE=$(git rev-parse origin/main)
git checkout -b "release-$RELEASE_VERSION"
```

## Step 2: Prepare the Stable Version

Record the old version and run bumpver without creating a commit:

```sh
OLD_VERSION=$(sed -n 's/^current_version = "\(.*\)"$/\1/p' pyproject.toml)
uvx tox run -e bumpver -- update --set-version "$RELEASE_VERSION" \
    --no-commit --no-tag-commit --no-push --no-fetch
```

Update only the local package version in `uv.lock`, using the same capture-and-restore method as the [development version guide](how-to-bump-dev-branch-version.md#step-2-update-uvlock):

```sh
uv lock
NEW_VERSION=$(sed -n '/^name = "dioptra-platform"$/{ n; s/^version = "\(.*\)"$/\1/p; }' uv.lock)
git checkout -- uv.lock
sed -i.bak '/^name = "dioptra-platform"$/{ n; s/^version = ".*"$/version = "'"$NEW_VERSION"'"/; }' uv.lock
rm uv.lock.bak
```

Update the stable references outside bumpver. These commands work with macOS and GNU sed; `.bak` files are temporary backups:

```sh
DEPLOYMENT_TEMPLATE=cookiecutter-templates/cookiecutter-dioptra-deployment/cookiecutter.json
DEPLOYMENT_DOCS=docs/source/how-to/setup-dioptra

sed -i.bak -E 's/^([[:space:]]*"container_tag": ")[^"]*/\1'"$RELEASE_VERSION"'/' \
    "$DEPLOYMENT_TEMPLATE"
sed -i.bak -E '/^- \*\*container_tag:\*\*/s/(default: ``)[^`]+/\1'"$RELEASE_VERSION"'/' \
    "$DEPLOYMENT_DOCS/prepare-deployment.rst"
sed -i.bak -E \
    '/^container_tag$/,/^docker_compose_path$/s/^(\*\*Default:\*\* ``)[^`]+/\1'"$RELEASE_VERSION"'/;
     s/^([[:space:]]*container_tag )\[[^]]+\]: .*/\1['"$RELEASE_VERSION"']: '"$RELEASE_VERSION"'/' \
    "$DEPLOYMENT_DOCS/reference/deployment-template-reference.rst"
sed -i.bak -E \
    's|^(docker pull ghcr[.]io/usnistgov/dioptra/[^:[:space:]]+:)[^[:space:]]+$|\1'"$RELEASE_VERSION"'|' \
    README.md
sed -i.bak -E 's/^dioptra-platform([<=>!~].*)?$/dioptra-platform=='"$RELEASE_VERSION"'/' \
    examples/examples-setup-requirements.txt

rm "$DEPLOYMENT_TEMPLATE.bak" "$DEPLOYMENT_DOCS/prepare-deployment.rst.bak" \
    "$DEPLOYMENT_DOCS/reference/deployment-template-reference.rst.bak" \
    README.md.bak examples/examples-setup-requirements.txt.bak
```

Keep third-party image defaults unchanged unless a separate update has been agreed. This retains `latest` for pgAdmin, MinIO, and Redis, the selected PostgreSQL major, and the existing MinIO client pin. The commands change only the platform requirement in the examples; other requirements remain unchanged.

Review the combined version diff and create one preparation commit:

```sh
git diff
git add -u
git commit -m "release $OLD_VERSION → $RELEASE_VERSION"
```

## Step 3: Merge with Main Locally

Create an integration branch at the recorded main revision and merge the preparation into it:

```sh
git checkout -b "release-$RELEASE_VERSION-integration" "$MAIN_BASE"
git merge --no-ff --no-commit --into-name main "release-$RELEASE_VERSION"
```

Resolve any conflicts, keeping stable versions and the intended dev changes while preserving applicable fixes already on main. Then stage the resolutions and use the default merge message:

```sh
git add -u
git commit
```

## Step 4: Open the Release Pull Request

Advance the release branch to the resolved merge and push it:

```sh
git checkout "release-$RELEASE_VERSION"
git merge --ff-only "release-$RELEASE_VERSION-integration"
git push --set-upstream origin "release-$RELEASE_VERSION"
```

Open a PR from `release-<version>` into main, titled `Release Dioptra <version>`. Leave the body empty or include short instructions for updating main after checks pass.

## Step 5: Wait for the Checks

Wait for all applicable release branch and PR checks to pass. Tox and Sphinx run on the branch push; Docker images and Frontend Playwright e2e run on the PR. Frontend checks run when their path filters match. If the release branch changes, wait for checks on the updated commit.

For workflow triggers and GitHub's temporary PR test merge, see [About Release Publishing](about-release-publishing.md#release-review-and-main-adoption).

## Step 6: Update Main

Fetch again, check that main has not advanced, then fast-forward it to the checked release commit:

```sh
git fetch origin &&
    test "$(git rev-parse origin/main)" = "$MAIN_BASE" &&
    git checkout main &&
    git merge --ff-only origin/main &&
    git merge --ff-only "release-$RELEASE_VERSION" &&
    git push origin main
```

If the main-base check fails, revise the candidate against current main and repeat its review and checks. If a merge or push fails, stop and resolve the cause. Do not force main.

## After Merging

Verify that the PR is marked **Merged** at the checked release commit. Wait for main CI to pass, then follow [How to Create a Release](how-to-create-a-release.md) to tag and publish it.

After publication, follow [How to Bump the Dev Branch Version](how-to-bump-dev-branch-version.md) when needed. Keep development versions, `dev` deployment defaults, and the unbounded example platform requirement on dev. Reconcile shared fixes separately.

Remove merged temporary branches with `git branch -d` when they are no longer needed. Remove the remote release branch only after confirming the PR is merged and no further work depends on it.
