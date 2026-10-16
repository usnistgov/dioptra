# How to Create a Patch Release

Use this guide to publish selected fixes from `dev` as a stable patch release without including the rest of the development branch.

For a release containing the full development branch, use [How to Merge Dev into Main](how-to-merge-dev-into-main.md). For the branch and version relationships, see [About Versioned Releases](about-versioned-releases.md).

- [Prerequisites](#prerequisites)
- [Step 1: Select the Fixes](#step-1-select-the-fixes)
- [Step 2: Prepare the Selected Fixes](#step-2-prepare-the-selected-fixes)
- [Step 3: Prepare and Commit the Stable Metadata](#step-3-prepare-and-commit-the-stable-metadata)
- [Step 4: Create the Integration Merge](#step-4-create-the-integration-merge)
- [Step 5: Open the Release Pull Request](#step-5-open-the-release-pull-request)
- [Step 6: Wait for the Checks](#step-6-wait-for-the-checks)
- [Step 7: Update Main](#step-7-update-main)
- [Step 8: Publish the Stable Release](#step-8-publish-the-stable-release)
- [After Merging](#after-merging)

## Prerequisites

-   A clean Dioptra clone and an up-to-date `dev` branch containing the fixes
-   [uv](https://docs.astral.sh/uv/) installed, with tox available through `uv tool install --python 3.11 tox --with tox-uv`.
-   The agreed stable version number
-   Permission to push a release branch and update protected `main` directly.

Run the commands from the clone root in the same Bash session. The example prepares `1.2.1` using one selected commit; replace the version and commit list for your release. Add further commits to the array in the order they must be applied. Do not squash the fixes or use GitHub's merge, squash, or rebase buttons for the release PR.

## Step 1: Select the Fixes

Fetch the current branches and choose the version and fixes to release.

```bash
git fetch origin
git checkout dev
git pull --ff-only origin dev

RELEASE_VERSION=1.2.1
RELEASE_BRANCH="release-$RELEASE_VERSION"
MAIN_BASE=$(git rev-parse origin/main)
PATCH_COMMITS=(
    581f0a6e844436447251be588dacc38c2d2c61b8
)
```

Select non-merge commits from dev and use their full IDs. List them in application order, including prerequisites identified during review of the fixes. Follow [How to Check Whether a Fix Is Already on a Branch](../git/how-to-check-whether-a-fix-is-on-a-branch.md) to check each fix against main before including it.

Check main's current version and confirm that `RELEASE_VERSION` is the next patch version, such as `1.2.0` to `1.2.1`:

```bash
git show "${MAIN_BASE}:pyproject.toml" | grep -m1 '^version = '
```

Follow [How to Check Published Versions](how-to-check-published-versions.md) to confirm that `RELEASE_VERSION` is unused in Git, PyPI, and all seven GHCR images. If it is already published, select another version before preparation.

## Step 2: Prepare the Selected Fixes

Create the release branch from the recorded main base and cherry-pick the selected commits in order.

```bash
git checkout -b "$RELEASE_BRANCH" "$MAIN_BASE"
git cherry-pick -x "${PATCH_COMMITS[@]}"
git log --reverse --oneline "$MAIN_BASE..HEAD"
```

Each selected fix must remain a separate commit with its source ID recorded by `-x`. Review conflicts and any backport adaptations against main. If a conflict, missing prerequisite, or compatibility concern changes the agreed patch set, stop for review before continuing. After resolving an accepted conflict, stage the affected files and run `git cherry-pick --continue`.

## Step 3: Prepare and Commit the Stable Metadata

Run bumpver after the fixes, without creating a commit or tag.

```bash
OLD_VERSION=$(sed -n 's/^current_version = "\(.*\)"$/\1/p' pyproject.toml)
uvx tox run -e bumpver -- update --set-version "$RELEASE_VERSION" \
    --no-commit --no-tag-commit --no-push --no-fetch
```

Update only the local package version in the lockfile. Capture the value written by uv, confirm that it matches the intended stable version, then restore the lockfile and apply that one field change.

```bash
uv lock
NEW_VERSION=$(sed -n '/^name = "dioptra-platform"$/{ n; s/^version = "\(.*\)"$/\1/p; }' uv.lock)
echo "$NEW_VERSION"
```

Confirm that the printed version matches `RELEASE_VERSION` before continuing. Then restore the lockfile and update its local package entry.

```bash
git checkout -- uv.lock
sed -i.bak '/^name = "dioptra-platform"$/{ n; s/^version = ".*"$/version = "'"$NEW_VERSION"'"/; }' uv.lock
rm uv.lock.bak
```

Update the stable references outside bumpver. These commands work with macOS and GNU sed; `.bak` files are temporary backups:

```bash
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

Keep dependency resolution and third-party image defaults unchanged unless a separate update is part of the agreed release.

Review the combined version diff and create one preparation commit:

```bash
git diff
git add -u
git commit -m "release $OLD_VERSION → $RELEASE_VERSION"
```

## Step 4: Create the Integration Merge

Create a separate integration branch at the recorded main base and merge the prepared release branch.

```bash
git checkout -b "$RELEASE_BRANCH-integration" "$MAIN_BASE"
git merge --no-ff --no-commit --into-name main "$RELEASE_BRANCH"
git commit --no-edit
git log --graph --oneline "$MAIN_BASE..HEAD"
```

The history should contain the individual fixes, one version preparation commit, and one merge into the recorded main base.

## Step 5: Open the Release Pull Request

Advance the release branch to that merge, record its exact revision, and push it:

```bash
git checkout "$RELEASE_BRANCH"
git merge --ff-only "$RELEASE_BRANCH-integration"
RELEASE_COMMIT=$(git rev-parse HEAD)
git push --set-upstream origin "$RELEASE_BRANCH"
```

Open a PR into main titled `Release Dioptra <version>`. Leave the body empty or include short instructions for updating main after checks pass.

## Step 6: Wait for the Checks

Wait for all applicable release branch and PR checks on `RELEASE_COMMIT` to pass. Tox and Sphinx run on the branch push; Docker images and Frontend Playwright e2e run on the PR. Frontend checks run when their path filters match. If the release branch changes, wait for checks on the updated commit.

For workflow triggers and GitHub's temporary PR test merge, see [About Release Publishing](about-release-publishing.md#release-review-and-main-adoption).

## Step 7: Update Main

Fetch again, check that main has not advanced and that the published release branch still identifies the checked candidate, then fast-forward main and push normally:

```bash
git fetch origin &&
    test "$(git rev-parse origin/main)" = "$MAIN_BASE" &&
    test "$(git rev-parse "origin/$RELEASE_BRANCH")" = "$RELEASE_COMMIT" &&
    git checkout main &&
    git merge --ff-only origin/main &&
    git merge --ff-only "$RELEASE_COMMIT" &&
    git push origin main
```

If the main-base check fails, revise the candidate against current main and repeat its review and checks. If a merge or push fails, stop and resolve the cause. Do not force push to main.

Stop if any command fails. If main advanced, revise the candidate against current main and repeat its review and affected checks. Do not force main or replace the checked integration merge with a squash, rebase, or GitHub merge-button commit.

Verify that remote main identifies `RELEASE_COMMIT` and that the PR is marked Merged at that commit. Wait for all applicable main checks before tagging.

## Step 8: Publish the Stable Release

Follow [How to Create a Release](how-to-create-a-release.md) to tag the checked main commit, monitor its workflows, and verify the published package and images. Complete that procedure before preparing the corresponding development release.

## After Merging

Verify that the PR is marked **Merged** at the checked release commit. Wait for main CI to pass, then follow [How to Create a Release](how-to-create-a-release.md) to tag and publish it.

After publication, refresh `dev` and reconcile shared fixes as needed, but do not reapply fixes that exist on both `dev` and `main` or merge stable version metadata into `dev`. After that, follow [Scenario 2 of How to Bump the Dev Branch Version](how-to-bump-dev-branch-version.md#scenario-2-incrementing-the-dev-tag) once for this patch release.

Remove merged temporary branches with `git branch -d` when they are no longer needed. Remove the remote release branch only after confirming the PR is merged and no further work depends on it.
