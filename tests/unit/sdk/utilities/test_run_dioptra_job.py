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

import uuid
from types import SimpleNamespace

import pytest
import structlog

from dioptra.sdk.utilities import run_dioptra_job


@pytest.mark.parametrize("association", [None, "invalid"])
def test_unusable_job_binding_fails_before_mlflow_activation(
    association: str | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prevent a worker from allocating a replacement for an unusable association.

    The API returns either no run ID or an ID the worker cannot use. The worker
    must stop before contacting MLflow so a recovered job always follows the
    run selection made by the API or by development maintenance.
    """

    def read_association(job_id: int) -> dict[str, str | None]:
        """Return the unusable association for the job under test.

        Args:
            job_id: The Dioptra job ID supplied by the worker.

        Returns:
            The API's run response with a deliberately unusable value.
        """
        return {"mlflowRunId": association}

    def unexpected_activation(**kwargs: object) -> None:
        """Fail if a worker with an unusable association asks MLflow to start a run.

        Args:
            **kwargs: Activation options that should never reach MLflow.
        """
        pytest.fail("The worker activated MLflow without a usable job association")

    monkeypatch.setattr(run_dioptra_job.mlflow, "start_run", unexpected_activation)
    client = SimpleNamespace(jobs=SimpleNamespace(get_mlflow_run_id=read_association))
    with pytest.raises(ValueError):
        run_dioptra_job._run_tracked_job(
            group_id=1,
            job_id=2,
            entrypoint_name="example",
            dioptra_client=client,
            context=run_dioptra_job.Context(),
            job_yaml={},
            job_parameters={},
            artifact_parameters={},
            artifact_tasks={},
            logger=structlog.stdlib.get_logger(),
        )


def test_worker_does_not_retry_activation_with_a_new_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Propagate activation failure after one attempt with the assigned MLflow ID.

    A worker reads a valid UUID from Dioptra, but the tracking backend rejects
    activation. Even with that backend error, logging must never start in an
    unassociated run.
    """
    run_id = uuid.uuid4()
    attempts = []

    def read_association(job_id: int) -> dict[str, str]:
        """Return the API's hyphenated UUID for this job.

        Args:
            job_id: The Dioptra job ID supplied by the worker.

        Returns:
            The job's API-assigned run ID.
        """
        return {"mlflowRunId": str(run_id)}

    def reject_activation(**kwargs: object) -> None:
        """Record the activation request and simulate a tracking backend error.

        Args:
            **kwargs: Activation options received by MLflow.

        Raises:
            RuntimeError: The simulated tracking backend rejects run activation.
        """
        attempts.append(kwargs.get("run_id"))
        raise RuntimeError("Simulated activation refusal")

    monkeypatch.setattr(run_dioptra_job.mlflow, "start_run", reject_activation)
    client = SimpleNamespace(jobs=SimpleNamespace(get_mlflow_run_id=read_association))
    with pytest.raises(RuntimeError):
        run_dioptra_job._run_tracked_job(
            group_id=1,
            job_id=2,
            entrypoint_name="example",
            dioptra_client=client,
            context=run_dioptra_job.Context(),
            job_yaml={},
            job_parameters={},
            artifact_parameters={},
            artifact_tasks={},
            logger=structlog.stdlib.get_logger(),
        )

    assert attempts == [run_id.hex]
