import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "monitor.py"
SPEC = importlib.util.spec_from_file_location("monitor", MODULE_PATH)
monitor = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
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


if __name__ == "__main__":
    unittest.main()
