# Lockfile refresh

The [Refresh uv.lock workflow](../../workflows/refresh-uv-lock.yml) regenerates dependency locks for `main` and `dev`. It invokes [refresh.py](refresh.py) to publish or retire a refresh candidate, then uses the [validation monitor](../monitor-refresh-validation/action.yml) to report checks on the candidate PR.

## Usage

Scheduled runs refresh both targets on Mondays at 08:37 UTC. Manual runs refresh one target. For example, this command previews a refresh of `main`.

```bash
gh workflow run refresh-uv-lock.yml --repo usnistgov/dioptra \
  -f target_branch=main -f dry_run=true
```

| Manual input | Values | Default | Effect |
| --- | --- | --- | --- |
| `target_branch` | `main`, `dev` | `dev` | Selects the source branch and PR base. |
| `dry_run` | `true`, `false` | `false` | When true, regenerates locally and describes intended operations without remote writes or validation dispatch. |

## Requirements

The runner needs Git, GitHub CLI, uv, and Python 3.11. The workflow installs uv and selects Python 3.11. Its token requires Actions, contents, and pull-request write permissions.

The helper requires a clean checkout of the selected target. Each target must contain this helper and the validation monitor before the default-branch workflow enables scheduled refreshes for both targets.

## Generated resources

| Target and PR base | Automation branch | Concurrency group |
| --- | --- | --- |
| `main` | `automation/refresh-uv-lock-main` | `refresh-uv-lock-main` |
| `dev` | `automation/refresh-uv-lock-dev` | `refresh-uv-lock-dev` |

The target job acquires its concurrency group before checkout and holds it through validation reporting. New requests leave the active refresh running but can replace a pending request for that target. Failure on one target does not cancel the other target's job.

## Refresh behavior

Each job records the checked-out source SHA and runs `uv lock --upgrade`. It accepts a change to `uv.lock` alone or a successful unchanged result.

| Result | PR and branch operations |
| --- | --- |
| `uv.lock` changes. | Recreate the target's automation branch from the checked-out source, commit only `uv.lock`, and open or update the same-repository PR with that head and base. Replace the previous validation report with the new candidate SHA and pending validation. |
| No changes remain, and the matching PR is open. | Close the obsolete PR with an explanation and cleanup marker in one update, then delete its automation branch. |
| No changes remain, and an earlier cleanup closed the PR but did not delete its branch. | Retry deletion only if the unmerged PR has the cleanup marker and the branch still has the recorded candidate SHA. |
| No matching PR or eligible cleanup record exists. | Report that the lockfile is current and leave any existing branch untouched. |
| Lock generation fails or another file changes. | Fail before publishing a candidate or cleaning up an existing one. |

Branch replacement and deletion use explicit `--force-with-lease` expectations. A branch update after inspection causes the push to fail rather than overwriting or deleting the updated branch. An already absent branch completes cleanup.

## Validation reporting

Changed candidates dispatch `tox-tests.yml` and `sphinx-docs.yml` against the automation branch. The monitor accepts runs matching the workflow, branch, candidate SHA, `workflow_dispatch` event, and dispatch time. It updates the PR body with results and run links. Failed, cancelled, or missing validation fails the refresh job. Dry runs do not dispatch or monitor validation.

Regenerate and revalidate after target changes to code, dependency declarations, or `uv.lock`. Documentation-only changes do not require regeneration.

## Failure recovery

| Failure | Maintainer action |
| --- | --- |
| Lock generation or changed-file guard fails. | Inspect the job output and resolve the cause on the target branch before rerunning. The existing candidate is retained. |
| Candidate validation fails. | Make compatibility or dependency-constraint fixes on the target branch and rerun the refresh. Changes made only on the automation branch are replaced by the next refresh. |
| PR closure fails. | Resolve the reported API or permission error and rerun. The branch is retained, and a rejected close does not create cleanup authority. |
| Branch deletion fails after PR closure. | Resolve the reported push error and rerun. The cleanup marker permits retrying deletion of the recorded candidate. |
| The automation branch has moved. | Inspect the new branch tip before taking further action. Cleanup will preserve a branch that no longer matches the recorded candidate. |

## Local checks

Run the focused helper and monitor tests from the repository root. They use temporary Git repositories and substituted GitHub responses without contacting the project repository.

```bash
uv run --no-project --python 3.11 --with pytest python -m pytest -q -c /dev/null \
  .github/actions/refresh-uv-lock/tests/test_refresh.py \
  .github/actions/monitor-refresh-validation/tests/test_monitor.py
```
