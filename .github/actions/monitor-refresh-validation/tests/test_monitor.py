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
import unittest
from datetime import datetime, timezone
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).parents[1] / "monitor.py"
SPEC = importlib.util.spec_from_file_location("monitor", MODULE_PATH)
assert SPEC is not None
assert SPEC.loader is not None
monitor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(monitor)


class MonitorRefreshValidationTests(unittest.TestCase):
    def test_replace_validation_section_replaces_existing_section(self) -> None:
        body = "\n".join(
            [
                "Intro",
                "",
                monitor.VALIDATION_START,
                "old",
                monitor.VALIDATION_END,
                "",
                "Tail",
            ]
        )

        result = monitor.replace_validation_section(body, "new")

        self.assertEqual(result, "Intro\n\nnew\n\nTail")

    def test_replace_validation_section_appends_new_section(self) -> None:
        result = monitor.replace_validation_section("Intro\n", "new")

        self.assertEqual(result, "Intro\n\nnew\n")

    def test_render_validation_section_reports_failed_jobs(self) -> None:
        results = [
            monitor.RunResult(
                spec=monitor.WorkflowSpec("tox-tests.yml", "Tox tests"),
                database_id=1,
                url="https://github.com/usnistgov/dioptra/actions/runs/1",
                status="completed",
                conclusion="failure",
                jobs=[
                    {
                        "name": "linting-and-style-checks (3.11, mypy)",
                        "status": "completed",
                        "conclusion": "failure",
                    }
                ],
            ),
            monitor.RunResult(
                spec=monitor.WorkflowSpec(
                    "sphinx-docs.yml",
                    "Sphinx documentation",
                ),
                database_id=2,
                url="https://github.com/usnistgov/dioptra/actions/runs/2",
                status="completed",
                conclusion="success",
            ),
        ]

        section = monitor.render_validation_section(
            results=results,
            head_branch="automation/refresh-uv-lock-dev",
            source_branch="dev",
        )

        self.assertIn(
            "failure, failed jobs: `linting-and-style-checks (3.11, mypy)`",
            section,
        )
        self.assertIn(
            "[Run 1](https://github.com/usnistgov/dioptra/actions/runs/1)", section
        )
        self.assertIn("Validation failed.", section)
        self.assertFalse(monitor.validation_succeeded(results))

    def test_render_validation_section_reports_success(self) -> None:
        results = [
            monitor.RunResult(
                spec=monitor.WorkflowSpec("tox-tests.yml", "Tox tests"),
                database_id=1,
                url="https://github.com/usnistgov/dioptra/actions/runs/1",
                status="completed",
                conclusion="success",
            )
        ]

        section = monitor.render_validation_section(
            results=results,
            head_branch="automation/refresh-uv-lock-dev",
            source_branch="dev",
        )

        self.assertIn("Validation completed successfully.", section)
        self.assertTrue(monitor.validation_succeeded(results))

    def test_timed_out_run_is_a_failure(self) -> None:
        result = monitor.RunResult(
            spec=monitor.WorkflowSpec("tox-tests.yml", "Tox tests"),
            database_id=1,
            status="in_progress",
            timed_out=True,
        )

        self.assertEqual(
            monitor.summarize_result(result), "timed out while in_progress"
        )
        self.assertFalse(monitor.validation_succeeded([result]))

    def test_missing_run_timeout_is_reported(self) -> None:
        result = monitor.RunResult(
            spec=monitor.WorkflowSpec("tox-tests.yml", "Tox tests"),
            timed_out=True,
        )

        self.assertEqual(monitor.summarize_result(result), "not found before timeout")
        self.assertFalse(monitor.validation_succeeded([result]))


@pytest.mark.parametrize(
    "different_field,value",
    [
        ("headBranch", "automation/refresh-uv-lock-main"),
        ("headSha", "another-sha"),
        ("event", "push"),
        ("createdAt", "2026-11-01T00:00:00Z"),
    ],
)
def test_discover_rejects_other_candidate_runs(monkeypatch, different_field, value):
    """Reject validation from another candidate or an earlier dispatch.

    API filtering alone does not prove identity. A response with the wrong branch,
    SHA, event or creation time must never supply this candidate's validation.
    """
    row = {
        "databaseId": 1,
        "status": "completed",
        "conclusion": "success",
        "event": "workflow_dispatch",
        "headBranch": "automation/refresh-uv-lock-dev",
        "headSha": "candidate-sha",
        "createdAt": "2026-11-02T00:00:01Z",
        "url": "https://github.com/example/dioptra/actions/runs/1",
    }
    row[different_field] = value

    def runs(args):
        assert args[args.index("--workflow") + 1] == "tox-tests.yml"
        return [row]

    monkeypatch.setattr(monitor, "run_gh_json", runs)
    assert (
        monitor.discover_run(
            repo="example/dioptra",
            spec=monitor.WORKFLOWS[0],
            head_branch="automation/refresh-uv-lock-dev",
            head_sha="candidate-sha",
            dispatch_started_at=datetime(2026, 11, 2, tzinfo=timezone.utc),
        )
        is None
    )


def test_discover_accepts_exact_candidate(monkeypatch):
    """Accept the dispatched workflow when all candidate identifiers match.

    Each workflow is queried separately. Its matching branch, SHA, event and
    dispatch time identify the run that the monitor may report.
    """
    row = {
        "databaseId": 1,
        "status": "completed",
        "conclusion": "success",
        "event": "workflow_dispatch",
        "headBranch": "automation/refresh-uv-lock-main",
        "headSha": "candidate-sha",
        "createdAt": "2026-11-02T00:00:01Z",
        "url": "https://github.com/example/dioptra/actions/runs/1",
    }

    def runs(args):
        assert args[args.index("--workflow") + 1] == "sphinx-docs.yml"
        return [row]

    monkeypatch.setattr(monitor, "run_gh_json", runs)
    result = monitor.discover_run(
        repo="example/dioptra",
        spec=monitor.WORKFLOWS[1],
        head_branch="automation/refresh-uv-lock-main",
        head_sha="candidate-sha",
        dispatch_started_at=datetime(2026, 11, 2, tzinfo=timezone.utc),
    )
    assert result.database_id == 1 and monitor.result_succeeded(result)


@pytest.mark.parametrize("conclusion", ["failure", "cancelled", "timed_out", "skipped"])
def test_unsuccessful_validation_never_reports_success(conclusion):
    """Keep failed, cancelled and incomplete validation visible to maintainers.

    A completed GitHub run without a success conclusion must fail the overall
    refresh even when the other validation workflow succeeds.
    """
    results = [
        monitor.RunResult(
            spec=monitor.WORKFLOWS[0], status="completed", conclusion=conclusion
        ),
        monitor.RunResult(
            spec=monitor.WORKFLOWS[1], status="completed", conclusion="success"
        ),
    ]
    assert not monitor.validation_succeeded(results)
    section = monitor.render_validation_section(
        results=results,
        head_branch="automation/refresh-uv-lock-main",
        source_branch="main",
    )
    assert "Validation failed." in section
    assert "Validation completed successfully." not in section


if __name__ == "__main__":
    unittest.main()
