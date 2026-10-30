# How to Create a Patch Release

Use this guide to publish selected fixes as a stable patch release without merging the rest of `dev`.

> [!NOTE]
> Deployments currently build the web frontend from the selected branch during initialization rather than from the Python package, so a PyPI patch release does not distribute pre-built frontend assets. Update this guide when the frontend row of the [implementation status](release-policy-implementation-status.md) applies now.

For a release containing the full `dev` branch, use [How to Merge Dev into Main](how-to-merge-dev-into-main.md). For background on branch and version relationships, see [About Versioned Releases](about-versioned-releases.md).

-   [Prerequisites](#prerequisites)
-   [Step 1: Select the Fixes](#step-1-select-the-fixes)
-   [Step 2: Cherry-Pick or Prepare the Fixes](#step-2-prepare-the-selected-fixes)
-   [Step 3: Prepare and Commit the Stable Metadata](#step-3-prepare-and-commit-the-stable-metadata)
-   [Step 4: Create the Pull Request Branch](#step-4-create-the-pull-request-branch)
-   [Step 5: Open the Release Pull Request](#step-5-open-the-release-pull-request)
-   [Step 6: Wait for the Checks](#step-6-wait-for-the-checks)
-   [Step 7: Update Main](#step-7-update-main)
-   [Step 8: Publish the Stable Release](#step-8-publish-the-stable-release)
-   [After Merging](#after-merging)

## Prerequisites

-   A clean Dioptra clone with access to `origin`
-   [uv](https://docs.astral.sh/uv/) installed, with tox available through `uv tool install --python 3.11 tox --with tox-uv`
-   The agreed patch version number and the list of fix commits to include
-   Permission to push a release branch and update protected `main` directly

Run the commands from the clone root in the same shell. The example prepares `1.2.1` using one cherry-picked commit; replace the version and commit list for your release. Do not squash the fixes or use GitHub's merge, squash, or rebase buttons for the release PR.

<a id="step-1-select-the-fixes"></a>

## Step 1: Select the Fixes

Fetch the current branches and set the target version and commits to cherry-pick:

```bash
git fetch origin
git checkout dev
git pull --ff-only origin dev

RELEASE_VERSION=1.2.1
RELEASE_BRANCH="release-$RELEASE_VERSION"
PR_BRANCH="$RELEASE_BRANCH-pr"
MAIN_BASE=$(git rev-parse origin/main)
PATCH_COMMITS=(
    581f0a6e844436447251be588dacc38c2d2c61b8
)
```

List non-merge commit hashes in the order they should be applied. Follow [How to Check Whether a Fix Is Already on a Branch](../git/how-to-check-whether-a-fix-is-on-a-branch.md) to confirm none of the commits are already on `main`.

Check `main`'s current version and verify via [How to Check Published Versions](how-to-check-published-versions.md) that `RELEASE_VERSION` is unused in Git, PyPI, and all seven GHCR images:

```bash
git show "${MAIN_BASE}:pyproject.toml" | grep -m1 '^version = '
```

<a id="step-2-prepare-the-selected-fixes"></a>

## Step 2: Cherry-Pick or Prepare the Fixes

Create the release branch from `MAIN_BASE` and cherry-pick the selected commits with `-x` to record their source commit IDs:

```bash
git checkout -b "$RELEASE_BRANCH" "$MAIN_BASE"
git cherry-pick -x "${PATCH_COMMITS[@]}"
git log --reverse --oneline "$MAIN_BASE..HEAD"
```

If you are authoring a fix directly on `$RELEASE_BRANCH` rather than cherry-picking from `dev`, commit each fix separately on `$RELEASE_BRANCH`. If a cherry-pick conflict arises, resolve it, stage the files, and run `git cherry-pick --continue`.

<a id="step-3-prepare-and-commit-the-stable-metadata"></a>

## Step 3: Prepare and Commit the Stable Metadata

Record the previous version and run bumpver without committing or tagging:

```bash
OLD_VERSION=$(sed -n 's/^current_version = "\(.*\)"$/\1/p' pyproject.toml)
uvx tox run -e bumpver -- update --set-version "$RELEASE_VERSION" \
    --no-commit --no-tag-commit --no-push --no-fetch
```

Update the stable version references outside bumpver, including the deployment template, its test expectation in `test_cruft_no_prompt.py`, the deployment documentation, `README.md`, and the examples requirement:

```bash
DEPLOYMENT_TEMPLATE=cookiecutter-templates/cookiecutter-dioptra-deployment/cookiecutter.json
DEPLOYMENT_TEST=tests/cookiecutter_dioptra_deployment/test_cruft_no_prompt.py
DEPLOYMENT_DOCS=docs/source/how-to/setup-dioptra

sed -i.bak -E 's/^([[:space:]]*"container_tag": ")[^"]*/\1'"$RELEASE_VERSION"'/' \
    "$DEPLOYMENT_TEMPLATE" "$DEPLOYMENT_TEST"
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

rm "$DEPLOYMENT_TEMPLATE.bak" "$DEPLOYMENT_TEST.bak" \
    "$DEPLOYMENT_DOCS/prepare-deployment.rst.bak" \
    "$DEPLOYMENT_DOCS/reference/deployment-template-reference.rst.bak" \
    README.md.bak examples/examples-setup-requirements.txt.bak
```

Check whether any fix modified dependency declarations in `pyproject.toml`:

```bash
git diff "$MAIN_BASE" -- pyproject.toml
```

-   **If only the version fields changed**, update only the local `dioptra-platform` version entry in `uv.lock`:

    ```bash
    sed -i.bak '/^name = "dioptra-platform"$/{ n; s/^version = ".*"$/version = "'"$RELEASE_VERSION"'"/; }' uv.lock
    rm uv.lock.bak
    uv lock --check
    ```

-   **If dependency declarations changed**, re-resolve the lockfile with `uv lock --upgrade` and review `git diff "$MAIN_BASE" -- uv.lock`.

Review the diff and commit the version bump:

```bash
git diff
git add -u
git commit -m "release $OLD_VERSION → $RELEASE_VERSION"
```

> [!NOTE]
> `test_cruft_no_prompt.py` clones the local repository's **committed** Git tree via `cruft create`. If you run `uvx tox run -e pytest-cookiecutter` locally, run it after creating this commit so it tests the updated template.

<a id="step-4-create-the-integration-merge"></a>

## Step 4: Create the Pull Request Branch

Create a local pull request branch at `MAIN_BASE` and merge the release branch into it with `--no-ff`, so the patch series lands on `main` as a single merge commit (`Merge branch 'release-<version>'`):

```bash
git checkout -b "$PR_BRANCH" "$MAIN_BASE"
git merge --no-ff -m "Merge branch '$RELEASE_BRANCH'" "$RELEASE_BRANCH"
git log --graph --oneline "$MAIN_BASE..HEAD"
```

The history between `MAIN_BASE` and `HEAD` should show the individual fix commits, one `release <old> → <new>` commit, and one merge commit.

<a id="step-5-open-the-release-pull-request"></a>

## Step 5: Open the Release Pull Request

Push the pull request branch to `origin` under the release branch name. The local release branch itself is not pushed:

```bash
git push --set-upstream origin "$PR_BRANCH:$RELEASE_BRANCH"
```

Open a pull request from `release-<version>` into `main` titled `Release Dioptra <version>`.

> [!WARNING]
> `origin/release-<version>` holds the pushed pull request branch, not your local `release-<version>` branch. Git rejects a normal push of the local branch, so do not force it. To add a change after pushing, commit it on the local `release-<version>` branch, then recreate and push the pull request branch with the last command block in Step 7.

<a id="step-6-wait-for-the-checks"></a>

## Step 6: Wait for the Checks

Wait for all release branch and pull request checks to pass (`Tox tests`, `Sphinx documentation`, `Docker images`, `Frontend Playwright e2e`, and `Frontend checks`). See [Release review and adoption](release-workflow-reference.md#release-review-and-main-adoption) for details.

<a id="step-7-update-main"></a>

## Step 7: Update Main

Confirm that `origin/main` has not advanced since `MAIN_BASE` (`git fetch origin && git log --oneline "$MAIN_BASE..origin/main"` should be empty), then fast-forward `main` to the pushed release branch and push:

```bash
git checkout main
git pull --ff-only origin main
git merge --ff-only "origin/$RELEASE_BRANCH"
git push origin main
```

If `origin/main` has advanced while the PR was open, do not force-push `main`. Instead, set `MAIN_BASE` to the new `origin/main` tip and merge it into the release branch. If that merge changes dependency declarations in `pyproject.toml` or `uv.lock`, repeat the lockfile handling in Step 3 and commit the result. Then recreate the pull request branch and wait for the PR checks to pass again:

```bash
git checkout -B "$PR_BRANCH" "$MAIN_BASE"
git merge --no-ff -m "Merge branch '$RELEASE_BRANCH'" "$RELEASE_BRANCH"
git push --force-with-lease origin "$PR_BRANCH:$RELEASE_BRANCH"
```

<a id="step-8-publish-the-stable-release"></a>

## Step 8: Publish the Stable Release

Verify that GitHub marks the release pull request as **Merged** and wait for the push checks on `main` to pass. Then follow [How to Create a Release](how-to-create-a-release.md) to tag `main`, monitor the publishing workflows, and verify the published package and container images.

<a id="after-merging"></a>

## After Merging

After stable publication is verified:

1.  If any fix was written directly on the release branch rather than cherry-picked from `dev`, cherry-pick it to `dev`.
2.  Update the [README installation image tags](how-to-bump-dev-branch-version.md#readme-installation-image-tags) on `dev` to the newly published version.
3.  Delete the temporary local branches (`git branch -d "$RELEASE_BRANCH" "$PR_BRANCH"`) and remove the remote release branch (`git push origin --delete "$RELEASE_BRANCH"`).
