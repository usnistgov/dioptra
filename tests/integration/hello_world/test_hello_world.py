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
import time

import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def test_hello_world(
    docker_client, dioptra_client, mlflow_client, workflows_tar_gz, dioptra_hosts
):
    def job_still_running(response):
        return response["status"] not in set(("failed", "finished"))

    response_experiment = dioptra_client.get_experiment_by_name(name="hello_world")

    if response_experiment is None or "Not Found" in response_experiment.get(
        "message", []
    ):
        response_experiment = dioptra_client.register_experiment(name="hello_world")

    response_queue = dioptra_client.get_queue_by_name(name="tensorflow_cpu")

    if response_queue is None or "Not Found" in response_queue.get("message", []):
        response_queue = dioptra_client.register_queue(name="tensorflow_cpu")

    response_hello_world = dioptra_client.submit_job(
        workflows_file=str(workflows_tar_gz),
        experiment_name="hello_world",
        entry_point="hello_world",
    )

    while job_still_running(response_hello_world):
        time.sleep(1)
        response_hello_world = dioptra_client.get_job_by_id(
            response_hello_world["jobId"]
        )

    hello_world_run = mlflow_client.get_run(response_hello_world["mlflowRunId"])
    tracked_metric_history = mlflow_client.get_metric_history(
        hello_world_run.info.run_id, "tracked_metric"
    )
    parameters = hello_world_run.data.params

    LOGGER.info("metrics", history=tracked_metric_history)
    LOGGER.info("parameters", **parameters)
    LOGGER.info("nginx container", attrs=docker_client.containers.get("nginx").attrs)

    assert response_hello_world["status"] == "finished"
    assert parameters["metric_first_record"] == "1.0"
    assert parameters["metric_second_record"] == "0.5"
    assert tracked_metric_history[0].value == 1.0
    assert tracked_metric_history[1].value == 0.5
