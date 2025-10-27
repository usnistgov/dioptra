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
import os
from typing import Any

import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.client import connect_json_dioptra_client, DioptraClient

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
def get_uri_for_model(
    model_name: str,
    model_version: int = -1
):
    dioptra_client = get_logged_in_session()
    models = dioptra_client.models.get(search=model_name, page_length=500)
    selected_model = None
    for model in models["data"]:
        if model["name"] == model_name:
            model_id = model["id"]
            if model_version >= 0:
                selected_model = dioptra_client.models.versions.get_by_id(
                    model_id=model_id, version_number=model_version
                )
            else:
                selected_model = model["latestVersion"]


    artifact = dioptra_client.artifacts.get_by_id(artifact_id=selected_model["artifact"]["id"])

    print(artifact)
    
    uri = (
        artifact["artifactUri"]
        if selected_model is not None
        else None
    )
    return uri


def post_metrics(
    metric_name: str,
    metric_value: float,
    job_id: str|int|None = None,
    metric_step: int|None = None
) -> dict[str, Any]:
    import math
    dioptra_client = get_logged_in_session()
    if math.isnan(metric_value):
        metric_value = -1
    if job_id == None:
        job_id = os.environ["__JOB_ID"]
    return dioptra_client.jobs.append_metric_by_id(
        job_id=job_id,
        metric_name=metric_name,
        metric_value=metric_value,
        metric_step=metric_step,
    )

def log_metrics(metrics: dict[str, float]) -> None:
    """Logs metrics to Dioptra for the current run.

    Args:
        metrics: A dictionary with the metrics to be logged. The keys are the metric
            names and the values are the metric values.
    """
    for metric_name, metric_value in metrics.items():
        post_metrics(metric_name=metric_name, metric_value=metric_value)
        LOGGER.info(
            "Logging metric",
            metric_name=metric_name,
            metric_value=metric_value,
        )

def get_logged_in_session() -> DioptraClient[dict[str, Any]]:
    url = os.environ["DIOPTRA_API"]
    dioptra_client = connect_json_dioptra_client(url)
    dioptra_client.auth.login(
        username=os.environ["DIOPTRA_WORKER_USERNAME"],
        password=os.environ["DIOPTRA_WORKER_PASSWORD"],
    )
    return dioptra_client
