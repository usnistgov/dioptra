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
"""Monitor validation workflows dispatched by the uv.lock refresh workflow."""

import argparse
import json
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VALIDATION_START = "<!-- refresh-validation:start -->"
VALIDATION_END = "<!-- refresh-validation:end -->"


@dataclass(frozen=True)
class WorkflowSpec:
    file_name: str
    display_name: str


@dataclass
class RunResult:
    spec: WorkflowSpec
    database_id: int | None = None
    url: str | None = None
    status: str = "not found"
    conclusion: str | None = None
    jobs: list[dict[str, Any]] = field(default_factory=list)
    timed_out: bool = False


WORKFLOWS = (
    WorkflowSpec(file_name="tox-tests.yml", display_name="Tox tests"),
    WorkflowSpec(file_name="sphinx-docs.yml", display_name="Sphinx documentation"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr-number", required=True)
    parser.add_argument("--head-branch", required=True)
    parser.add_argument("--source-branch", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--dispatch-started-at", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=3600)
    parser.add_argument("--poll-interval-seconds", type=int, default=30)
    return parser.parse_args()


def parse_github_timestamp(value: str) -> datetime:
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"

    return datetime.fromisoformat(value).astimezone(timezone.utc)


def run_gh_json(args: list[str]) -> Any:
    result = subprocess.run(
        ["gh", *args],
        check=True,
        capture_output=True,
        text=True,
    )

    if not result.stdout.strip():
        return None

    return json.loads(result.stdout)


def run_gh(args: list[str]) -> None:
    subprocess.run(["gh", *args], check=True)


def discover_run(
    *,
    repo: str,
    spec: WorkflowSpec,
    head_branch: str,
    head_sha: str,
    dispatch_started_at: datetime,
) -> RunResult | None:
    runs = run_gh_json(
        [
            "run",
            "list",
            "--repo",
            repo,
            "--workflow",
            spec.file_name,
            "--branch",
            head_branch,
            "--event",
            "workflow_dispatch",
            "--commit",
            head_sha,
            "--limit",
            "20",
            "--json",
            "databaseId,status,conclusion,event,headBranch,headSha,createdAt,url",
        ]
    )

    matches = [
        run
        for run in runs
        if run.get("event") == "workflow_dispatch"
        and run.get("headBranch") == head_branch
        and run.get("headSha") == head_sha
        and parse_github_timestamp(run["createdAt"]) >= dispatch_started_at
    ]
    if not matches:
        return None

    matches.sort(key=lambda run: parse_github_timestamp(run["createdAt"]), reverse=True)
    match = matches[0]
    return RunResult(
        spec=spec,
        database_id=match["databaseId"],
        url=match["url"],
        status=match["status"],
        conclusion=match.get("conclusion"),
    )


def refresh_run(repo: str, result: RunResult) -> RunResult:
    if result.database_id is None:
        return result

    run = run_gh_json(
        [
            "run",
            "view",
            str(result.database_id),
            "--repo",
            repo,
            "--json",
            "databaseId,status,conclusion,url,jobs",
        ]
    )
    result.status = run["status"]
    result.conclusion = run.get("conclusion")
    result.url = run["url"]
    result.jobs = run.get("jobs", [])
    return result


def poll_runs(
    *,
    repo: str,
    head_branch: str,
    head_sha: str,
    dispatch_started_at: datetime,
    timeout_seconds: int,
    poll_interval_seconds: int,
) -> list[RunResult]:
    results = {spec.file_name: RunResult(spec=spec) for spec in WORKFLOWS}
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        for spec in WORKFLOWS:
            result = results[spec.file_name]
            if result.database_id is None:
                discovered = discover_run(
                    repo=repo,
                    spec=spec,
                    head_branch=head_branch,
                    head_sha=head_sha,
                    dispatch_started_at=dispatch_started_at,
                )
                if discovered is not None:
                    result = discovered

            if result.database_id is not None:
                result = refresh_run(repo, result)

            results[spec.file_name] = result

        if all(result.status == "completed" for result in results.values()):
            return list(results.values())

        remaining_seconds = deadline - time.monotonic()
        if remaining_seconds > 0:
            time.sleep(min(poll_interval_seconds, remaining_seconds))

    for result in results.values():
        if result.status != "completed":
            result.timed_out = True

    return list(results.values())


def failed_job_names(jobs: list[dict[str, Any]]) -> list[str]:
    return [
        job["name"]
        for job in jobs
        if job.get("status") == "completed"
        and job.get("conclusion") not in {"success", "skipped", None}
    ]


def markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def markdown_code(value: str) -> str:
    escaped = value.replace("`", "\\`")
    return f"`{escaped}`"


def result_succeeded(result: RunResult) -> bool:
    return result.status == "completed" and result.conclusion == "success"


def validation_succeeded(results: list[RunResult]) -> bool:
    return all(result_succeeded(result) for result in results)


def summarize_result(result: RunResult) -> str:
    if result.database_id is None:
        if result.timed_out:
            return "not found before timeout"

        return "not found"

    if result.status != "completed":
        if result.timed_out:
            return f"timed out while {result.status}"

        return result.status

    conclusion = result.conclusion or "completed"
    if conclusion == "success":
        return "success"

    jobs = failed_job_names(result.jobs)
    if not jobs:
        return conclusion

    formatted_jobs = ", ".join(markdown_code(job) for job in jobs)
    return f"{conclusion}, failed jobs: {formatted_jobs}"


def render_validation_section(
    *,
    results: list[RunResult],
    head_branch: str,
    source_branch: str,
) -> str:
    lines = [
        VALIDATION_START,
        "## Validation",
        "",
        "| Workflow | Status | Run |",
        "| --- | --- | --- |",
    ]

    for result in results:
        run_link = ""
        if result.database_id is not None and result.url is not None:
            run_link = f"[Run {result.database_id}]({result.url})"

        lines.append(
            "| "
            f"{markdown_cell(result.spec.display_name)} | "
            f"{markdown_cell(summarize_result(result))} | "
            f"{run_link} |"
        )

    lines.append("")
    if validation_succeeded(results):
        lines.append(
            "Validation completed successfully. This pull request only refreshes "
            "`uv.lock`."
        )
    else:
        lines.append(
            f"Validation failed. Do not fix this on `{head_branch}`; the refresh "
            f"workflow recreates that branch from `{source_branch}` on each run. "
            f"Make compatibility fixes or dependency constraint changes on "
            f"`{source_branch}`, then rerun the lockfile refresh workflow."
        )

    lines.append(VALIDATION_END)
    return "\n".join(lines)


def replace_validation_section(body: str, validation_section: str) -> str:
    start_index = body.find(VALIDATION_START)
    end_index = body.find(VALIDATION_END)

    if start_index != -1 and end_index != -1 and start_index < end_index:
        end_index += len(VALIDATION_END)
        return f"{body[:start_index]}{validation_section}{body[end_index:]}"

    body = body.rstrip()
    if body:
        return f"{body}\n\n{validation_section}\n"

    return f"{validation_section}\n"


def get_pr_body(repo: str, pr_number: str) -> str:
    pr = run_gh_json(
        [
            "pr",
            "view",
            pr_number,
            "--repo",
            repo,
            "--json",
            "body",
        ]
    )
    return pr.get("body") or ""


def update_pr_body(repo: str, pr_number: str, body: str) -> None:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
        f.write(body)
        body_path = Path(f.name)

    try:
        run_gh(
            [
                "pr",
                "edit",
                pr_number,
                "--repo",
                repo,
                "--body-file",
                str(body_path),
            ]
        )
    finally:
        body_path.unlink(missing_ok=True)


def main() -> None:
    args = parse_args()
    dispatch_started_at = parse_github_timestamp(args.dispatch_started_at)

    results = poll_runs(
        repo=args.repository,
        head_branch=args.head_branch,
        head_sha=args.head_sha,
        dispatch_started_at=dispatch_started_at,
        timeout_seconds=args.timeout_seconds,
        poll_interval_seconds=args.poll_interval_seconds,
    )
    validation_section = render_validation_section(
        results=results,
        head_branch=args.head_branch,
        source_branch=args.source_branch,
    )
    pr_body = get_pr_body(args.repository, args.pr_number)
    update_pr_body(
        args.repository,
        args.pr_number,
        replace_validation_section(pr_body, validation_section),
    )

    print(validation_section)
    if not validation_succeeded(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
