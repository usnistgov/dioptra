# How to Merge Dev into Main

Use this guide to prepare a major or minor release that brings the planned `dev` changes into `main`. Tagging and publication are covered in [How to Create a Release](how-to-create-a-release.md). For background on how `main` and `dev` interact, see [About Versioned Releases](about-versioned-releases.md#branch-life-cycles).

For a patch release containing only selected fixes, use [How to Create a Patch Release](how-to-create-a-patch-release.md).

-   [Prerequisites](#prerequisites)
-   [Step 1: Create the Release Branch](#step-1-create-the-release-branch)
-   [Step 2: Merge Dev into the Release Branch](#step-2-merge-dev-into-the-release-branch)
-   [Step 3: Prepare the Stable Version and Lockfile](#step-3-prepare-the-stable-version-and-lockfile)
-   [Step 4: Create the Pull Request Branch](#step-4-create-the-pull-request-branch)
-   [Step 5: Open the Release Pull Request](#step-5-open-the-release-pull-request)
-   [Step 6: Wait for the Checks](#step-6-wait-for-the-checks)
-   [Step 7: Update Main](#step-7-update-main)
-   [After Merging](#after-merging)

## Prerequisites

-   A clean Dioptra clone with access to `origin`
-   [uv](https://docs.astral.sh/uv/) installed, with tox available through `uv tool install --python 3.11 tox --with tox-uv`
-   The agreed stable version number and a `dev` branch containing the planned release content
-   Permission to push a release branch and update protected `main` directly

Run the commands from the clone root in the same shell. The examples use `1.3.0`; substitute the version you are preparing. This procedure assembles the release on a `release-<version>` branch created from `main`, merges it with `--no-ff` into a local `release-<version>-pr` branch that also starts from `main`, pushes that branch to `origin` as `release-<version>` for review, and fast-forwards `main` to the merge commit after PR checks pass. Do not use GitHub's merge, squash, or rebase buttons for the release PR.

<a id="step-1-create-the-release-branch"></a>

## Step 1: Create the Release Branch

Fetch the current branches, update `main`, record its current version, and create the release branch from `main`:

```sh
git fetch origin
git checkout main
git pull --ff-only origin main

RELEASE_VERSION=1.3.0
RELEASE_BRANCH="release-$RELEASE_VERSION"
PR_BRANCH="$RELEASE_BRANCH-pr"
MAIN_BASE=$(git rev-parse HEAD)
MERGE_BASE=$(git merge-base "$MAIN_BASE" origin/dev)
OLD_VERSION=$(sed -n 's/^current_version = "\(.*\)"$/\1/p' pyproject.toml)
git checkout -b "$RELEASE_BRANCH"
```

Follow [How to Check Published Versions](how-to-check-published-versions.md) to confirm that `RELEASE_VERSION` is unused in Git, PyPI, and all seven GHCR images before proceeding.

<a id="step-2-merge-dev"></a>

## Step 2: Merge Dev into the Release Branch

Inspect the commits that landed on `main` since `main` and `dev` diverged:

```sh
git log --oneline "$MERGE_BASE..$MAIN_BASE"
git log --oneline "$MERGE_BASE..$MAIN_BASE" -- src/frontend/package.json src/frontend/package-lock.json
```

Confirm that each fix on `main` (including any npm dependency fix shown by the second command) is already represented on `dev`, using [How to Check Whether a Fix Is Already on a Branch](../git/how-to-check-whether-a-fix-is-on-a-branch.md). If `dev` is missing a fix from `main`, either carry that fix to `dev` first or preserve it when resolving merge conflicts below.

Merge `origin/dev` into the release branch without committing:

```sh
git merge --no-ff --no-commit origin/dev
```

Resolve any conflicts so the candidate contains the intended changes from both branches. Keep `main`'s `uv.lock` as the starting point for Step 3:

```sh
git checkout "$MAIN_BASE" -- uv.lock
git status
```

Stage the resolved files and commit the merge:

```sh
git add -u
git commit -m "Merge branch 'dev' into $RELEASE_BRANCH"
```

<a id="step-3-prepare-the-stable-version"></a>

## Step 3: Prepare the Stable Version and Lockfile

Run bumpver without committing:

```sh
uvx tox run -e bumpver -- update --set-version "$RELEASE_VERSION" \
    --no-commit --no-tag-commit --no-push --no-fetch
```

Update the stable version references outside bumpver, including the deployment template, its test expectation in `test_cruft_no_prompt.py`, the deployment documentation, `README.md`, and the examples requirement:

```sh
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

Keep third-party image defaults (`postgres`, `redis`, `minio`, `minio/mc`, `pgadmin4`) unchanged unless an update was planned for this release.

Next, check whether `pyproject.toml` dependency declarations differ from `main`:

```sh
git diff "$MAIN_BASE" -- pyproject.toml
```

Ignore the version fields.

-   **If dependency declarations changed** (`dependencies`, optional dependencies, dependency groups, or `[tool.uv]` settings), re-resolve the lockfile and review the diff against `main`:

    ```sh
    uv lock --upgrade
    git diff --stat "$MAIN_BASE" -- uv.lock
    ```

-   **If dependency declarations match `main`**, update only the `dioptra-platform` version entry in `uv.lock`:

    ```sh
    sed -i.bak '/^name = "dioptra-platform"$/{ n; s/^version = ".*"$/version = "'"$RELEASE_VERSION"'"/; }' uv.lock
    rm uv.lock.bak
    uv lock --check
    ```

Review the diff and commit the version bump (`$OLD_VERSION` is the prior stable version recorded from `main` in Step 1):

```sh
git diff
git add -u
git commit -m "release $OLD_VERSION → $RELEASE_VERSION"
```

> [!NOTE]
> `test_cruft_no_prompt.py` clones the local repository's **committed** Git tree via `cruft create`. If you run `uvx tox run -e pytest-cookiecutter` locally, run it after creating this commit so it tests the updated template.

<a id="step-4-create-the-integration-merge"></a>
<a id="step-3-merge-with-main-locally"></a>

## Step 4: Create the Pull Request Branch

Create a local pull request branch at `MAIN_BASE` and merge the release branch into it with `--no-ff`, so the release lands on `main` as a single merge commit (`Merge branch 'release-<version>'`):

```sh
git checkout -b "$PR_BRANCH" "$MAIN_BASE"
git merge --no-ff -m "Merge branch '$RELEASE_BRANCH'" "$RELEASE_BRANCH"
git log --graph --oneline "$MAIN_BASE..HEAD"
```

Because the release branch started from `MAIN_BASE`, this merge completes without conflicts. Its first parent is `MAIN_BASE` and its second parent is the `release <old> → <new>` commit.

<a id="step-4-open-the-release-pull-request"></a>
<a id="step-5-open-the-release-pull-request"></a>

## Step 5: Open the Release Pull Request

Push the pull request branch to `origin` under the release branch name. The local release branch itself is not pushed:

```sh
git push --set-upstream origin "$PR_BRANCH:$RELEASE_BRANCH"
```

Open a pull request from `release-<version>` into `main` titled `Release Dioptra <version>`.

> [!WARNING]
> `origin/release-<version>` holds the pushed pull request branch, not your local `release-<version>` branch. Git rejects a normal push of the local branch, so do not force it. To add a change after pushing, commit it on the local `release-<version>` branch, then recreate and push the pull request branch with the last command block in Step 7.

<a id="step-5-wait-for-the-checks"></a>

## Step 6: Wait for the Checks

Wait for all release branch and pull request checks to pass (`Tox tests`, `Sphinx documentation`, `Docker images`, `Frontend Playwright e2e`, and `Frontend checks`). See [Release review and adoption](release-workflow-reference.md#release-review-and-main-adoption) for details on the triggered workflows.

<a id="step-6-update-main"></a>

## Step 7: Update Main

Confirm that `origin/main` has not advanced since `MAIN_BASE` (`git fetch origin && git log --oneline "$MAIN_BASE..origin/main"` should be empty), then fast-forward `main` to the pushed release branch and push:

```sh
git checkout main
git pull --ff-only origin main
git merge --ff-only "origin/$RELEASE_BRANCH"
git push origin main
```

If `origin/main` has advanced while the PR was open, do not force-push `main`. Instead, set `MAIN_BASE` to the new `origin/main` tip and merge it into the release branch. If that merge changes dependency declarations in `pyproject.toml` or `uv.lock`, repeat the lockfile handling in Step 3 and commit the result. Then recreate the pull request branch and wait for the PR checks to pass again:

```sh
git checkout -B "$PR_BRANCH" "$MAIN_BASE"
git merge --no-ff -m "Merge branch '$RELEASE_BRANCH'" "$RELEASE_BRANCH"
git push --force-with-lease origin "$PR_BRANCH:$RELEASE_BRANCH"
```

<a id="after-merging"></a>

## After Merging

Verify that GitHub marks the release pull request as **Merged** and wait for the push checks on `main` to pass. Then follow [How to Create a Release](how-to-create-a-release.md) to tag and publish the release.

After publication is verified:

1.  Advance the `dev` branch target version using [How to Bump the Dev Branch Version](how-to-bump-dev-branch-version.md).
2.  Delete the temporary local branches (`git branch -d "$RELEASE_BRANCH" "$PR_BRANCH"`) and remove the remote release branch (`git push origin --delete "$RELEASE_BRANCH"`).
