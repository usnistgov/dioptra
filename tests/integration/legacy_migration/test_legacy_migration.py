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
import math
import time

import structlog
from structlog.stdlib import BoundLogger

from tests.integration.legacy_migration.utils import (
    job_still_running,
    mlflow_run_id_is_not_known,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def test_legacy_migration(
    testbed_hosts,
    testbed_client,
    mlflow_client,
    workflows_tar_gz,
    train_entrypoint_response,
):
    # Run "fgm" entrypoint job
    response_fgm_shallow_net = testbed_client.submit_job(
        workflows_file=str(workflows_tar_gz),
        experiment_name="mnist",
        entry_point="fgm",
        entry_point_kwargs=" ".join(
            ["-P model_name=mnist_shallow_net", "-P model_version=1"]
        ),
    )

    while mlflow_run_id_is_not_known(response_fgm_shallow_net):
        time.sleep(1)
        response_fgm_shallow_net = testbed_client.get_job_by_id(
            response_fgm_shallow_net["jobId"]
        )

    # Run "infer" entrypoint job
    response_shallow_net_infer_shallow_net = testbed_client.submit_job(
        workflows_file=str(workflows_tar_gz),
        experiment_name="mnist",
        entry_point="infer",
        entry_point_kwargs=" ".join(
            [
                f"-P run_id={response_fgm_shallow_net['mlflowRunId']}",
                "-P model_name=mnist_shallow_net",
                "-P model_version=1",
            ]
        ),
        depends_on=response_fgm_shallow_net["jobId"],
    )

    while job_still_running(response_fgm_shallow_net) or job_still_running(
        response_shallow_net_infer_shallow_net
    ):
        time.sleep(1)
        response_fgm_shallow_net = testbed_client.get_job_by_id(
            response_fgm_shallow_net["jobId"]
        )
        response_shallow_net_infer_shallow_net = testbed_client.get_job_by_id(
            response_shallow_net_infer_shallow_net["jobId"]
        )

    # Collect run results
    shallow_train_run = mlflow_client.get_run(train_entrypoint_response["mlflowRunId"])
    fgm_shallow_net_run = mlflow_client.get_run(response_fgm_shallow_net["mlflowRunId"])
    shallow_net_infer_shallow_net_run = mlflow_client.get_run(
        response_shallow_net_infer_shallow_net["mlflowRunId"]
    )

    shallow_train_parameters = shallow_train_run.data.params
    fgm_shallow_net_parameters = fgm_shallow_net_run.data.params
    shallow_net_infer_shallow_net_parameters = (
        shallow_net_infer_shallow_net_run.data.params
    )

    shallow_train_metrics = shallow_train_run.data.metrics
    fgm_shallow_net_metrics = fgm_shallow_net_run.data.metrics
    shallow_net_infer_shallow_net_metrics = (
        shallow_net_infer_shallow_net_run.data.metrics
    )

    LOGGER.info("train entrypoint parameters", **shallow_train_parameters)
    LOGGER.info("train entrypoint metrics", **shallow_train_metrics)
    LOGGER.info("fgm entrypoint parameters", **fgm_shallow_net_parameters)
    LOGGER.info("fgm entrypoint metrics", **fgm_shallow_net_metrics)
    LOGGER.info(
        "infer entrypoint parameters", **shallow_net_infer_shallow_net_parameters
    )
    LOGGER.info("infer entrypoint metrics", **shallow_net_infer_shallow_net_metrics)

    # Check that all jobs ran to a successful completion
    assert response_fgm_shallow_net["status"] == "finished"
    assert response_fgm_shallow_net["status"] == "finished"
    assert response_shallow_net_infer_shallow_net["status"] == "finished"

    # Check that mean FGM distance metrics are non-zero
    assert fgm_shallow_net_metrics["l_infinity_norm_mean"] > 0
    assert fgm_shallow_net_metrics["l_1_norm_mean"] > 0
    assert fgm_shallow_net_metrics["l_2_norm_mean"] > 0
    assert fgm_shallow_net_metrics["cosine_similarity_mean"] > 0
    assert fgm_shallow_net_metrics["euclidean_distance_mean"] > 0
    assert fgm_shallow_net_metrics["manhattan_distance_mean"] > 0
    assert fgm_shallow_net_metrics["wasserstein_distance_mean"] > 0

    # Check that eps parameter is close to the average Linf norm
    assert math.isclose(
        float(fgm_shallow_net_parameters["eps"]),
        float(fgm_shallow_net_metrics["l_infinity_norm_mean"]),
        abs_tol=1e-5,
    )

    # Check that the FGM attack reduced the accuracy and AUC metrics
    assert (
        shallow_train_metrics["accuracy"]
        > shallow_net_infer_shallow_net_metrics["accuracy"]
    )
    assert shallow_train_metrics["auc"] > shallow_net_infer_shallow_net_metrics["auc"]
