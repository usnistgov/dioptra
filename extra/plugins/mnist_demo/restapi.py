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
def get_uri_for_model(model_name, model_version=-1):
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

    uri = (
        selected_model["artifact"]["artifactUri"]
        if selected_model is not None
        else None
    )
    return uri


def get_uris_for_job(
    job_id: str | int
) -> list[str]:
    dioptra_client = get_logged_in_session()
    job = dioptra_client.jobs.get_by_id(job_id)
    return [artifact["artifactUri"] for artifact in job["artifacts"]]


def get_uris_for_artifacts(
    artifact_ids: list[int]
) -> list[dict[str, Any]]:
    dioptra_client = get_logged_in_session()
    return [dioptra_client.artifacts.get_by_id(artifact_id=aid) for aid in artifact_ids]


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


def get_logged_in_session() -> DioptraClient[dict[str, Any]]:
    url = os.environ["DIOPTRA_API"]
    dioptra_client = connect_json_dioptra_client(url)
    dioptra_client.auth.login(
        username=os.environ["DIOPTRA_WORKER_USERNAME"],
        password=os.environ["DIOPTRA_WORKER_PASSWORD"],
    )
    return dioptra_client


def upload_model_to_restapi(
    name: str, 
    source_uri: str, 
    job_id: str | int,
):
    version = 0
    model_id = 0

    dioptra_client = get_logged_in_session()
    models = dioptra_client.models.get(search=name, page_length=500)

    LOGGER.info("requesting models from RESTAPI", response=models)

    for model in models["data"]:
        # check whether to create a new model
        if model["name"] == name:
            model_id = model["id"]
            if model["latestVersion"] != None:
                version = model["latestVersion"]["versionNumber"] + 1

    if version == 0 and model_id == 0:
        model = dioptra_client.models.create(
            group_id=1, name=name, description=f"{name} model"
        )
        model_id = model["id"]
        LOGGER.info("new model created", response=model)

    artifact = dioptra_client.artifacts.create(
        group_id=1, description=f"{name} model artifact", job_id=job_id, uri=source_uri
    )
    LOGGER.info("artifact", response=artifact)

    model_version = dioptra_client.models.versions.create(
        model_id=model_id,
        artifact_id=artifact["id"],
        description=f"{name} model version",
    )
    LOGGER.info("model created", response=model_version)


def upload_artifact_to_restapi(
    source_uri: str,
    job_id: str | int,
):
    dioptra_client = get_logged_in_session()
    artifact = dioptra_client.artifacts.create(
        group_id=1,
        description=f"artifact for job {job_id}",
        job_id=job_id,
        uri=source_uri,
    )
    LOGGER.info("artifact", response=artifact)
