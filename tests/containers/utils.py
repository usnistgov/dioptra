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
from __future__ import annotations

import os

import pytest

from docker import DockerClient

try:
    from typing import TypedDict

except ImportError:
    from typing_extensions import TypedDict


DIOPTRA_IMAGES = [
    "mlflow-tracking",
    "nginx",
    "pytorch-cpu",
    "pytorch-gpu",
    "restapi",
    "tensorflow2-cpu",
    "tensorflow2-gpu",
]
ENV_DIOPTRA_TEST_CONTAINER = os.getenv("DIOPTRA_TEST_CONTAINER")
TEST_WORKDIR: str = "/test_workdir"

CONTAINER_FIXTURE_PARAMS = [
    pytest.param(
        x,
        marks=pytest.mark.skipif(
            ENV_DIOPTRA_TEST_CONTAINER is not None and ENV_DIOPTRA_TEST_CONTAINER != x,
            reason="Parameter doesn't match the value specified in environment "
            "variable DIOPTRA_TEST_CONTAINER",
        ),
    )
    for x in DIOPTRA_IMAGES
]


class DioptraImages(TypedDict, total=False):
    mlflow_tracking: str
    nginx: str
    pytorch_cpu: str
    pytorch_gpu: str
    restapi: str
    tensorflow2_cpu: str
    tensorflow2_gpu: str
    mlflow_tracking1_12_1: str
    restapi_py37: str
    tensorflow21_cpu: str


def start_container(client: DockerClient, image: str, user: str | int | None = None):
    image_fullname, _ = image.split(":")
    image_name = image_fullname.split("/")[-1]

    return client.containers.run(
        image=image,
        hostname=f"test_{image_name}",
        entrypoint="/bin/bash",
        user=user,
        remove=True,
        tty=True,
        detach=True,
        tmpfs={TEST_WORKDIR: ""},
        working_dir=TEST_WORKDIR,
    )
