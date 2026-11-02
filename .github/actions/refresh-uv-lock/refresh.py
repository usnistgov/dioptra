#!/usr/bin/env python
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
"""Regenerate one target's lockfile and publish or retire its refresh candidate.

Run from a clean checkout of main or dev after acquiring the target's workflow
concurrency group. Dry runs inspect GitHub state but make no remote writes.
Validation monitoring stays in the workflow and holds the same concurrency group.
"""

import argparse
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def command(*args: str) -> str:
    """Run a checked command and return its output, preserving failure diagnostics."""
    return subprocess.run(
        args, check=True, stdout=subprocess.PIPE, text=True
    ).stdout.rstrip("\n")


def gh_json(*args: str) -> Any:
    return json.loads(command("gh", *args))


def remote_sha(branch: str) -> str:
    """Return the branch tip, or an empty string only when the ref is absent."""
    result = command("git", "ls-remote", "--heads", "origin", f"refs/heads/{branch}")
    return result.split()[0] if result else ""


def matching_pulls(repository: str, target: str, branch: str) -> list[dict[str, Any]]:
    """Find same-repository PRs, independently checking the API's filtered results."""
    owner = repository.split("/")[0]
    pages = gh_json(
        "api",
        "--method",
        "GET",
        "--paginate",
        "--slurp",
        f"repos/{repository}/pulls",
        "-f",
        "state=all",
        "-f",
        f"head={owner}:{branch}",
        "-f",
        f"base={target}",
        "-f",
        "per_page=100",
    )
    return [
        pr
        for page in pages
        for pr in page
        if pr["head"]["ref"] == branch
        and pr["base"]["ref"] == target
        and (pr["head"].get("repo") or {}).get("full_name") == repository
        and (pr["base"].get("repo") or {}).get("full_name") == repository
    ]


def edit_body(repository: str, number: int, body: str, *args: str) -> None:
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "body.md"
        path.write_text(body, encoding="utf-8")
        command(
            "gh",
            "pr",
            "edit",
            str(number),
            "--repo",
            repository,
            "--body-file",
            str(path),
            *args,
        )


def cleanup_marker(target: str, sha: str) -> str:
    # Bind retries to the candidate that was closed, not just a reusable branch name.
    return f"<!-- uv-lock-refresh-cleanup:{target}:{sha} -->"


def close_candidate(repository: str, target: str, pr: dict[str, Any]) -> None:
    """Record cleanup provenance in the same request that closes the obsolete PR.

    A rejected close must not leave a marker that could later authorize deletion
    after a maintainer closes the PR manually.
    """
    explanation = (
        f"uv lock --upgrade produces no changes on {target}; "
        "this refresh candidate is obsolete."
    )
    body = (pr.get("body") or "").rstrip()
    marker = cleanup_marker(target, pr["head"]["sha"])
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "close.json"
        path.write_text(
            json.dumps(
                {"state": "closed", "body": f"{body}\n\n{explanation}\n\n{marker}\n"}
            ),
            encoding="utf-8",
        )
        updated = gh_json(
            "api",
            "--method",
            "PATCH",
            f"repos/{repository}/pulls/{pr['number']}",
            "--input",
            str(path),
        )
    if updated["state"] != "closed" or updated.get("merged_at"):
        raise RuntimeError("The obsolete refresh PR was not closed unmerged.")


def delete_candidate(branch: str, expected_sha: str) -> None:
    current_sha = remote_sha(branch)
    if not current_sha:
        print(f"{branch} is already absent.")
        return
    if current_sha != expected_sha:
        raise RuntimeError(f"Refusing to delete {branch}: its tip changed.")
    command(
        "git",
        "push",
        f"--force-with-lease=refs/heads/{branch}:{expected_sha}",
        "origin",
        f":refs/heads/{branch}",
    )
    print(f"Deleted {branch} at {expected_sha}.")


def retire_candidate(
    repository: str,
    target: str,
    branch: str,
    pulls: list[dict[str, Any]],
    dry_run: bool,
) -> None:
    """Close the obsolete PR before deleting its branch, with SHA-bound retries.

    A closed, unmerged PR bearing this cleanup path's marker permits retrying a
    failed deletion only while the remote branch still has that candidate's SHA.
    Unmarked closed PRs and branches without an owned PR confer no deletion right.
    """
    opened = [pr for pr in pulls if pr["state"] == "open"]
    if len(opened) > 1:
        raise RuntimeError("More than one matching open refresh PR.")
    if opened:
        pr = opened[0]
        sha = pr["head"]["sha"]
        current_sha = remote_sha(branch)
        if current_sha and current_sha != sha:
            raise RuntimeError("Refresh branch no longer matches the obsolete PR.")
        if dry_run:
            print(
                f"Would mark and close PR #{pr['number']}, then delete {branch} at {sha}."
            )
            return
        close_candidate(repository, target, pr)
        delete_candidate(branch, sha)
        return

    retry_cleanup(target, branch, pulls, dry_run)


def retry_cleanup(
    target: str,
    branch: str,
    pulls: list[dict[str, Any]],
    dry_run: bool,
) -> None:
    """Finish deletion only for an unmerged PR closed by this cleanup path."""
    current_sha = remote_sha(branch)
    retry = next(
        (
            pr
            for pr in pulls
            if pr["state"] == "closed"
            and not pr.get("merged_at")
            and pr["head"]["sha"] == current_sha
            and cleanup_marker(target, current_sha) in (pr.get("body") or "")
        ),
        None,
    )
    if retry is not None:
        if dry_run:
            print(
                f"Would retry deletion of {branch} at {current_sha} "
                f"for cleanup-closed PR #{retry['number']}."
            )
        else:
            delete_candidate(branch, current_sha)
    else:
        print(f"uv.lock is current for {target}; no owned cleanup target remains.")


def publish_candidate(
    repository: str,
    target: str,
    branch: str,
    source_sha: str,
    pulls: list[dict[str, Any]],
) -> dict[str, str]:
    """Publish only uv.lock and dispatch validation for the resulting commit."""
    opened = [pr for pr in pulls if pr["state"] == "open"]
    if len(opened) > 1:
        raise RuntimeError("More than one matching open refresh PR.")
    previous_sha = remote_sha(branch)
    command("git", "config", "user.name", "github-actions[bot]")
    command(
        "git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"
    )
    command("git", "checkout", "-B", branch)
    command("git", "add", "--", "uv.lock")
    command("git", "commit", "-m", "build: refresh uv.lock")
    sha = command("git", "rev-parse", "HEAD")
    command(
        "git",
        "push",
        f"--force-with-lease=refs/heads/{branch}:{previous_sha}",
        "origin",
        f"HEAD:refs/heads/{branch}",
    )

    title = f"build: refresh uv.lock for {target}"
    body = (
        f"This pull request refreshes `uv.lock` for `{target}` using "
        "`uv lock --upgrade` within the constraints in `pyproject.toml`.\n\n"
        f"Source commit: `{source_sha}`. Candidate commit: `{sha}`.\n\n"
        "The refresh workflow "
        "dispatches tox tests and the Sphinx documentation build and reports "
        "their exact-commit results here. Human review and successful validation "
        "are required before merging.\n\n"
        f"If code, dependency declarations or `uv.lock` change on `{target}`, "
        "regenerate and revalidate before merging. Documentation-only changes "
        "do not require regeneration.\n\n"
        "<!-- refresh-validation:start -->\n"
        "## Validation\n\n"
        f"Validation is pending for `{sha}` on `{branch}`.\n"
        "<!-- refresh-validation:end -->\n"
    )
    if opened:
        number = opened[0]["number"]
        # Replace the body so results and cleanup markers from older candidates vanish.
        edit_body(repository, number, body, "--title", title)
    else:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "body.md"
            path.write_text(body, encoding="utf-8")
            url = command(
                "gh",
                "pr",
                "create",
                "--repo",
                repository,
                "--base",
                target,
                "--head",
                branch,
                "--title",
                title,
                "--body-file",
                str(path),
            )
        number = gh_json("pr", "view", url, "--repo", repository, "--json", "number")[
            "number"
        ]

    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for workflow in ("tox-tests.yml", "sphinx-docs.yml"):
        command(
            "gh", "workflow", "run", workflow, "--repo", repository, "--ref", branch
        )
    return {"head_sha": sha, "pr_number": str(number), "dispatch_started_at": started}


def refresh(repository: str, target: str, dry_run: bool) -> dict[str, str]:
    """Refresh a clean target checkout; fail before remote writes on invalid changes.

    Unsupported targets, a dirty starting checkout, lock failures and changes to
    anything except uv.lock raise an error before PR or branch mutation. Return
    workflow outputs needed to monitor the exact published candidate.
    """
    if target not in {"main", "dev"}:
        raise ValueError(f"Unsupported target: {target}")
    branch = f"automation/refresh-uv-lock-{target}"
    if command("git", "status", "--porcelain=v1", "--untracked-files=all"):
        raise RuntimeError("Refresh requires a clean target checkout.")
    source_sha = command("git", "rev-parse", "HEAD")
    print(f"Refreshing {target} from {source_sha}.")
    command("uv", "lock", "--upgrade")
    status = command("git", "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if status and status != " M uv.lock\0":
        raise RuntimeError(f"uv lock --upgrade changed unexpected files: {status!r}")
    changed = bool(status)
    outputs = {"changed": str(changed).lower(), "source_sha": source_sha}
    pulls = matching_pulls(repository, target, branch)
    if not changed:
        retire_candidate(repository, target, branch, pulls, dry_run)
    elif dry_run:
        print(command("git", "diff", "--stat", "--", "uv.lock"))
        print(
            f"Would recreate {branch} from {target} at {source_sha}, commit only "
            "uv.lock, open or update its PR, and dispatch tox-tests.yml and "
            "sphinx-docs.yml for the new candidate SHA."
        )
    else:
        outputs.update(publish_candidate(repository, target, branch, source_sha, pulls))
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--target", choices=("main", "dev"), required=True)
    parser.add_argument("--dry-run", choices=("true", "false"), default="false")
    args = parser.parse_args()
    outputs = refresh(args.repository, args.target, args.dry_run == "true")
    with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as stream:
        for name, value in outputs.items():
            stream.write(f"{name}={value}\n")


if __name__ == "__main__":
    main()
