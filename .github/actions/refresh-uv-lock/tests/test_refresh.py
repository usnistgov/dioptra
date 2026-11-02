# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United States Code Section 105, works of NIST employees are not
# subject to copyright protection in the United States. However, NIST may hold
# international copyright in software created by its employees and domestic
# copyright (or licensing rights) in portions of software that were assigned or
# licensed to NIST. To the extent that NIST holds copyright in this software, it is
# being made available under the Creative Commons Attribution 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode
import importlib.util
import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "refresh.py"
SPEC = importlib.util.spec_from_file_location("refresh", MODULE_PATH)
refresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(refresh)
MONITOR_PATH = MODULE_PATH.parent.parent / "monitor-refresh-validation" / "monitor.py"
MONITOR_SPEC = importlib.util.spec_from_file_location("monitor", MONITOR_PATH)
monitor = importlib.util.module_from_spec(MONITOR_SPEC)
MONITOR_SPEC.loader.exec_module(monitor)
REPOSITORY = "example/dioptra"


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    """Use real Git histories and a local remote; substitute only uv and GitHub."""
    remote = tmp_path / "origin.git"
    work = tmp_path / "work"

    def git(*args):
        return subprocess.run(
            ["git", *args], check=True, capture_output=True, text=True
        ).stdout.strip()

    git("init", "--bare", str(remote))
    git("init", "-b", "dev", str(work))
    monkeypatch.chdir(work)
    git("config", "user.name", "Test maintainer")
    git("config", "user.email", "test@example.com")
    Path("pyproject.toml").write_text("[project]\nname = 'example'\n")
    Path("uv.lock").write_text("old lock\n")
    Path("README.md").write_text("Documentation\n")
    git("add", ".")
    git("commit", "-m", "Initial source")
    git("remote", "add", "origin", str(remote))
    git("push", "origin", "dev", "dev:main")
    state = {"pulls": [], "calls": [], "fail": None, "change": "lock"}
    real_command = refresh.command

    def command(*args):
        state["calls"].append(args)
        if args[0] == "uv":
            if state["fail"] == "lock":
                raise RuntimeError("Injected lock failure")
            if state["change"] == "lock":
                Path("uv.lock").write_text("upgraded lock\n")
            elif state["change"] == "unexpected":
                Path("untracked.txt").write_text("unexpected output\n")
            return ""
        if args[0] == "git":
            if state["fail"] == "delete" and args[-1].startswith(":refs/heads/"):
                raise RuntimeError("Injected deletion failure")
            return real_command(*args)
        assert args[0] == "gh", "The test must not run an external client."
        return github_response(state, git, args)

    monkeypatch.setattr(refresh, "command", command)
    return state, git


def github_response(state, git, args):
    """Model PR state and dispatch responses without contacting GitHub."""
    if args[1] == "api" and "PATCH" in args:
        return close_response(state, args)
    if args[1] == "api":
        # Return even unrelated rows so ownership checks must inspect identities.
        return json.dumps([deepcopy(state["pulls"])])
    if args[1:3] == ("workflow", "run"):
        if state["fail"] == "dispatch":
            raise RuntimeError("Injected dispatch failure")
        return ""
    if args[1:3] == ("pr", "create"):
        target = args[args.index("--base") + 1]
        sha = git("rev-parse", "HEAD")
        pr = pull(target, sha, number=42)
        pr["body"] = Path(args[args.index("--body-file") + 1]).read_text()
        state["pulls"].append(pr)
        return "https://github.com/example/dioptra/pull/42"
    if args[1:3] == ("pr", "view"):
        return json.dumps({"number": 42})
    pr = next(pr for pr in state["pulls"] if str(pr["number"]) == args[3])
    if args[2] == "edit":
        pr["body"] = Path(args[args.index("--body-file") + 1]).read_text()
    else:
        raise AssertionError(args)
    return ""


def close_response(state, args):
    """Apply the close request as one PR update, or reject it before any update."""
    number = args[args.index("PATCH") + 1].rsplit("/", 1)[1]
    pr = next(pr for pr in state["pulls"] if str(pr["number"]) == number)
    if state["fail"] == "close":
        raise RuntimeError("Injected close failure")
    update = json.loads(Path(args[args.index("--input") + 1]).read_text())
    pr.update(update)
    return json.dumps(pr)


def pull(target, sha, *, number=7, state="open", repository=REPOSITORY):
    return {
        "number": number,
        "state": state,
        "body": "old validation results",
        "merged_at": None,
        "head": {
            "ref": f"automation/refresh-uv-lock-{target}",
            "sha": sha,
            "repo": {"full_name": repository},
        },
        "base": {"ref": target, "repo": {"full_name": REPOSITORY}},
    }


def old_candidate(git, target="dev"):
    branch = f"automation/refresh-uv-lock-{target}"
    git("checkout", "-B", branch, target if target == "dev" else "origin/main")
    Path("uv.lock").write_text("previous candidate\n")
    git("add", "uv.lock")
    git("commit", "-m", "Previous refresh")
    sha = git("rev-parse", "HEAD")
    git("push", "origin", branch)
    git("checkout", "dev")
    return sha


def mutations(state):
    return [
        args
        for args in state["calls"]
        if args[:2]
        in {
            ("git", "push"),
            ("gh", "workflow"),
        }
        or args[:3] in {("gh", "pr", "create"), ("gh", "pr", "edit")}
        or args[:2] == ("gh", "api")
        and "PATCH" in args
    ]


@pytest.mark.parametrize("target", ["main", "dev"])
def test_changed_candidate_is_exact_lock_only_commit(checkout, target):
    """Publish the selected branch's lock change and validate that precise candidate.

    The opposite target has its own candidate. A refresh must leave it untouched,
    commit only uv.lock from the selected source, and dispatch both validations.
    """
    state, git = checkout
    other = "main" if target == "dev" else "dev"
    other_sha = old_candidate(git, other)
    state["pulls"] = [pull(other, other_sha)]
    git("checkout", "--detach", f"origin/{target}")
    source = git("rev-parse", "HEAD")
    result = refresh.refresh(REPOSITORY, target, False)
    candidate = result["head_sha"]
    assert git("rev-parse", f"{candidate}^") == source
    assert (
        git("diff-tree", "--no-commit-id", "--name-only", "-r", candidate) == "uv.lock"
    )
    assert refresh.remote_sha(f"automation/refresh-uv-lock-{target}") == candidate
    assert refresh.remote_sha(f"automation/refresh-uv-lock-{other}") == other_sha
    assert state["pulls"][0]["body"] == "old validation results"
    body = state["pulls"][-1]["body"]
    assert candidate in body and source in body and f"`{target}`" in body
    dispatches = [c for c in state["calls"] if c[:3] == ("gh", "workflow", "run")]
    assert {c[3] for c in dispatches} == {"tox-tests.yml", "sphinx-docs.yml"}
    assert all(
        c[c.index("--ref") + 1] == f"automation/refresh-uv-lock-{target}"
        for c in dispatches
    )
    assert result["pr_number"] == "42" and result["dispatch_started_at"]


def test_new_target_replaces_existing_candidate_and_validation(checkout):
    """Replace an older PR candidate from the current target instead of its old parent.

    Advancing source code before refresh must carry that code into the candidate
    and discard the previous candidate's validation report and cleanup marker.
    """
    state, git = checkout
    old = old_candidate(git)
    pr = pull("dev", old)
    pr["body"] += refresh.cleanup_marker("dev", old)
    state["pulls"] = [pr]
    Path("source.py").write_text("updated_source = True\n")
    git("add", "source.py")
    git("commit", "-m", "Update target")
    git("push", "origin", "dev")
    source = git("rev-parse", "HEAD")
    result = refresh.refresh(REPOSITORY, "dev", False)
    assert git("rev-parse", "HEAD^") == source
    assert git("show", "HEAD:source.py") == "updated_source = True"
    assert "old validation results" not in pr["body"]
    assert "uv-lock-refresh-cleanup:" not in pr["body"]
    assert result["head_sha"] in pr["body"] and result["pr_number"] == "7"
    assert not any(c[:3] == ("gh", "pr", "create") for c in state["calls"])


@pytest.mark.parametrize("target", ["main", "dev"])
def test_unchanged_closes_then_deletes_only_owned_candidate(checkout, target):
    """Retire only the selected target's obsolete PR after a successful no-change run.

    A same-named head from a fork, a wrong base and the opposite target must all
    remain unchanged; the owned PR must close before any branch deletion.
    """
    state, git = checkout
    sha = old_candidate(git, target)
    other = "main" if target == "dev" else "dev"
    other_sha = old_candidate(git, other)
    owned = pull(target, sha)
    fork = pull(target, sha, number=8, repository="fork/dioptra")
    wrong_base = pull(target, sha, number=9)
    wrong_base["base"]["ref"] = other
    unrelated = [fork, wrong_base, pull(other, other_sha, number=10)]
    state.update(change="none", pulls=[owned, *unrelated])
    result = refresh.refresh(REPOSITORY, target, False)
    assert result["changed"] == "false"
    assert owned["state"] == "closed"
    assert not refresh.remote_sha(f"automation/refresh-uv-lock-{target}")
    assert refresh.remote_sha(f"automation/refresh-uv-lock-{other}") == other_sha
    assert all(
        pr["state"] == "open" and pr["body"] == "old validation results"
        for pr in unrelated
    )
    calls = mutations(state)
    assert next(
        i for i, c in enumerate(calls) if c[:2] == ("gh", "api") and "PATCH" in c
    ) < next(i for i, c in enumerate(calls) if c[:2] == ("git", "push"))


@pytest.mark.parametrize("has_branch", [False, True])
def test_unchanged_without_owned_pr_does_not_write(checkout, has_branch):
    """An unowned branch alone never permits deletion.

    Both an absent candidate and a branch without a matching PR must finish a
    successful no-change refresh without PR, branch or validation writes.
    """
    state, git = checkout
    sha = old_candidate(git) if has_branch else ""
    state["change"] = "none"
    refresh.refresh(REPOSITORY, "dev", False)
    assert not mutations(state)
    assert refresh.remote_sha("automation/refresh-uv-lock-dev") == sha


@pytest.mark.parametrize("changed", ["lock", "none"])
def test_dry_run_makes_no_remote_writes(checkout, changed, capsys):
    """Preview changed and unchanged paths without publishing or retiring candidates.

    Existing obsolete candidates and validation reports must survive the preview,
    and the report must describe the operations a real run would perform.
    """
    state, git = checkout
    sha = old_candidate(git)
    state.update(change=changed, pulls=[pull("dev", sha)])
    refresh.refresh(REPOSITORY, "dev", True)
    assert not mutations(state)
    assert refresh.remote_sha("automation/refresh-uv-lock-dev") == sha
    assert state["pulls"][0]["state"] == "open"
    assert "Would" in capsys.readouterr().out


@pytest.mark.parametrize("failure", ["lock", "unexpected"])
def test_regeneration_failure_prevents_all_mutation(checkout, failure):
    """Lock command failure or unexpected changed files cannot retire an old PR.

    An existing candidate is retained, and no publishing or validation dispatch
    occurs when regeneration cannot establish a successful lock-only result.
    """
    state, git = checkout
    sha = old_candidate(git)
    state["pulls"] = [pull("dev", sha)]
    state["fail" if failure == "lock" else "change"] = failure
    with pytest.raises(RuntimeError):
        refresh.refresh(REPOSITORY, "dev", False)
    assert not mutations(state)
    assert refresh.remote_sha("automation/refresh-uv-lock-dev") == sha
    assert state["pulls"][0]["state"] == "open"


def test_close_failure_preserves_branch(checkout):
    """A rejected PR close must never be followed by branch deletion.

    A rejected update must leave the PR open without a cleanup marker. A later
    manual closure cannot authorize deleting that branch as a cleanup retry.
    """
    state, git = checkout
    sha = old_candidate(git)
    state.update(change="none", fail="close", pulls=[pull("dev", sha)])
    with pytest.raises(RuntimeError, match="close failure"):
        refresh.refresh(REPOSITORY, "dev", False)
    assert state["pulls"][0]["state"] == "open"
    assert refresh.remote_sha("automation/refresh-uv-lock-dev") == sha
    assert not any(c[:2] == ("git", "push") for c in mutations(state))
    assert refresh.cleanup_marker("dev", sha) not in state["pulls"][0]["body"]
    state["pulls"][0]["state"] = "closed"
    state.update(fail=None, calls=[])
    refresh.refresh(REPOSITORY, "dev", False)
    assert not mutations(state)
    assert refresh.remote_sha("automation/refresh-uv-lock-dev") == sha


def test_delete_failure_retries_cleanup_closed_candidate(checkout):
    """Recover a partial cleanup without requiring the PR to remain open.

    After a successful close and failed deletion, the recorded candidate SHA
    permits the next unchanged run to remove only the remaining obsolete branch.
    """
    state, git = checkout
    sha = old_candidate(git)
    state.update(change="none", fail="delete", pulls=[pull("dev", sha)])
    with pytest.raises(RuntimeError, match="deletion failure"):
        refresh.refresh(REPOSITORY, "dev", False)
    assert state["pulls"][0]["state"] == "closed"
    assert refresh.remote_sha("automation/refresh-uv-lock-dev") == sha
    state.update(fail=None, calls=[])
    refresh.refresh(REPOSITORY, "dev", False)
    assert not refresh.remote_sha("automation/refresh-uv-lock-dev")
    assert not any(c[:2] == ("gh", "api") and "PATCH" in c for c in mutations(state))


@pytest.mark.parametrize("closed_kind", ["unmarked", "merged", "replaced"])
def test_closed_pr_does_not_authorize_unrelated_deletion(checkout, closed_kind):
    """A historical PR cannot authorize deletion of an unrelated branch.

    Cleanup retries reject an unmarked closure, a merged candidate and a branch
    that has moved since the cleanup marker was recorded.
    """
    state, git = checkout
    sha = old_candidate(git)
    pr = pull("dev", sha, state="closed")
    if closed_kind != "unmarked":
        pr["body"] = refresh.cleanup_marker("dev", sha)
    if closed_kind == "merged":
        pr["merged_at"] = "2026-11-02T00:00:00Z"
    if closed_kind == "replaced":
        git("push", "--force", "origin", "dev:automation/refresh-uv-lock-dev")
    state.update(change="none", pulls=[pr])
    before = refresh.remote_sha("automation/refresh-uv-lock-dev")
    refresh.refresh(REPOSITORY, "dev", False)
    assert not mutations(state)
    assert refresh.remote_sha("automation/refresh-uv-lock-dev") == before


def test_absent_branch_is_successful_cleanup(checkout):
    """Closing an obsolete PR succeeds even if its branch is already absent.

    Branch absence is an idempotent result; GitHub PR closure still occurs, with
    no unnecessary or misleading deletion attempt.
    """
    state, git = checkout
    state.update(change="none", pulls=[pull("dev", git("rev-parse", "HEAD"))])
    refresh.refresh(REPOSITORY, "dev", False)
    assert state["pulls"][0]["state"] == "closed"
    assert not any(c[:2] == ("git", "push") for c in mutations(state))


def test_unsupported_target_rejected_before_commands(checkout):
    """Reject a manual target outside main and dev before mutation is possible.

    The CLI choice and this direct-call check ensure invalid input cannot select
    a new remote branch or reach lock regeneration.
    """
    state, _ = checkout
    with pytest.raises(ValueError, match="Unsupported target"):
        refresh.refresh(REPOSITORY, "release", False)
    assert not state["calls"]


def test_dirty_source_rejected_before_lock_regeneration(checkout):
    """Prevent pre-existing changes from being published as refreshed dependencies.

    A dirty source checkout must stop before uv runs or any remote mutation.
    """
    state, _ = checkout
    Path("README.md").write_text("Uncommitted source\n")
    with pytest.raises(RuntimeError, match="clean target"):
        refresh.refresh(REPOSITORY, "dev", False)
    assert not mutations(state)
    assert not any(c[0] == "uv" for c in state["calls"])


def test_cleanup_retry_dry_run_preserves_branch(checkout):
    """Previewing a partial cleanup cannot complete its pending branch deletion.

    A cleanup-closed PR and matching branch allow deletion on a real retry. The
    dry run must describe that operation while preserving the branch.
    """
    state, git = checkout
    sha = old_candidate(git)
    pr = pull("dev", sha, state="closed")
    pr["body"] = refresh.cleanup_marker("dev", sha)
    state.update(change="none", pulls=[pr])
    refresh.refresh(REPOSITORY, "dev", True)
    assert not mutations(state)
    assert refresh.remote_sha("automation/refresh-uv-lock-dev") == sha


@pytest.mark.parametrize("changed", ["none", "lock"])
def test_remote_race_is_rejected_by_explicit_lease(checkout, monkeypatch, changed):
    """A remote update after inspection cannot be overwritten or deleted.

    Inject a new remote tip immediately before the publication or deletion push.
    The real local Git remote must reject the stale lease and retain that tip.
    """
    state, git = checkout
    sha = old_candidate(git)
    state.update(change=changed, pulls=[pull("dev", sha)])
    original_command = refresh.command
    replacement = git("rev-parse", "dev")

    def racing_command(*args):
        if args[:2] == ("git", "push"):
            git("push", "--force", "origin", "dev:automation/refresh-uv-lock-dev")
        return original_command(*args)

    monkeypatch.setattr(refresh, "command", racing_command)
    with pytest.raises(subprocess.CalledProcessError):
        refresh.refresh(REPOSITORY, "dev", False)
    assert refresh.remote_sha("automation/refresh-uv-lock-dev") == replacement
    assert not any(c[:3] == ("gh", "workflow", "run") for c in state["calls"])


def test_dispatch_failure_leaves_pending_candidate_and_fails(checkout):
    """A dispatch failure must not be mistaken for successful candidate validation.

    The published PR retains a pending report tied to its SHA and the helper
    raises, preventing the workflow from reporting a successful refresh.
    """
    state, git = checkout
    state["fail"] = "dispatch"
    with pytest.raises(RuntimeError, match="dispatch failure"):
        refresh.refresh(REPOSITORY, "dev", False)
    candidate = refresh.remote_sha("automation/refresh-uv-lock-dev")
    body = state["pulls"][0]["body"]
    assert candidate == git("rev-parse", "HEAD") and candidate in body
    assert "Validation is pending" in body
    assert "Validation completed successfully" not in body


@pytest.mark.parametrize("conclusion", ["success", "failure"])
def test_final_report_replaces_pending_status(checkout, conclusion):
    """Keep one current validation status from publication through completion.

    A published candidate begins with pending validation. Completing either a
    successful or failed validation must replace that status while preserving
    the source and candidate identifiers and the stable PR introduction.
    """
    state, _ = checkout
    outputs = refresh.refresh(REPOSITORY, "dev", False)
    body = state["pulls"][0]["body"]
    assert "Validation is pending" in body
    assert monitor.VALIDATION_START in body and monitor.VALIDATION_END in body
    before, pending = body.split(monitor.VALIDATION_START, 1)
    _, after = pending.split(monitor.VALIDATION_END, 1)
    assert "Validation is pending" not in before + after
    results = [
        monitor.RunResult(spec=spec, status="completed", conclusion=conclusion)
        for spec in monitor.WORKFLOWS
    ]
    report = monitor.render_validation_section(
        results=results,
        head_branch="automation/refresh-uv-lock-dev",
        source_branch="dev",
    )
    updated = monitor.replace_validation_section(body, report)
    assert "Validation is pending" not in updated
    assert updated.startswith(before) and updated.endswith(after)
    assert updated.count(monitor.VALIDATION_START) == 1
    assert outputs["head_sha"] in updated and outputs["source_sha"] in updated
    expected = (
        "Validation completed successfully."
        if conclusion == "success"
        else "Validation failed."
    )
    assert expected in updated
