# How to Check Whether a Fix Is Already on a Branch

Use this guide to check whether another branch contains a fix, including a cherry-picked copy with a different commit ID.

-   [Prerequisites](#prerequisites)
-   [Step 1: Select the Fix and Target Branch](#step-1-select-the-fix-and-target-branch)
-   [Step 2: Look for the Original Commit](#step-2-look-for-the-original-commit)
-   [Step 3: Look for an Equivalent Patch](#step-3-look-for-an-equivalent-patch)
-   [Step 4: Compare the Code If Needed](#step-4-compare-the-code-if-needed)

## Prerequisites

-   A clone of the repository
-   The commit ID of the fix to check, which must be a non-merge commit

Run the commands from the clone root in the same shell. The example checks a fix from `dev` against `main`; replace the commit ID and target branch as needed. These commands leave the working tree unchanged.

## Step 1: Select the Fix and Target Branch

Fetch the current branches and set the fix and target:

```sh
git fetch origin
FIX=581f0a6e844436447251be588dacc38c2d2c61b8
TARGET=origin/main
```

## Step 2: Look for the Original Commit

List the remote branches whose history contains the original commit:

```sh
git branch --remotes --contains "$FIX"
```

If `origin/main` is listed, the original commit is already in main's history. Otherwise, continue to Step 3 to look for a backport with a different commit ID.

## Step 3: Look for an Equivalent Patch

Compare the selected commit's changes with the target branch's history:

```sh
git cherry -v "$TARGET" "$FIX" "$FIX^"
```

A line beginning with `-` means Git found an equivalent patch in the target history. A line beginning with `+` means it did not. No output means the original commit is already in the target history.

The `"$FIX^"` argument limits the comparison to the selected commit. Repeat the command for each fix you are considering. See [git cherry](https://git-scm.com/docs/git-cherry) for the patch comparison rules.

## Step 4: Compare the Code If Needed

If Git found no match but the fix may have been adapted, compare the original change with the current target code:

```sh
git show "$FIX"
git show "$TARGET:path/to/affected-file"
```

Replace `path/to/affected-file` with a file changed by the fix, and repeat the second command for other affected files. Check whether the target code already implements the correction shown in the original patch. Git's patch comparison does not recognize every equivalent implementation.

Also check the current code if a matched fix may have been reverted later. A commit or patch in the history does not establish that its changes are still present. If the result remains unclear, review the fix with its author before backporting it.
