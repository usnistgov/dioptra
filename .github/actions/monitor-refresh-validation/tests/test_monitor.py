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
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
