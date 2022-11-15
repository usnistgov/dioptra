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
from pathlib import Path

import pytest
from mlflow.tracking import MlflowClient

import docker
from tests.integration.download_data import download_data
from tests.integration.utils import TestDioptraClient

DIOPTRA_CACHE_DIR: Path = Path("/tmp") / "dioptra-cache"


@pytest.fixture
def mlflow_client(monkeypatch):
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://localhost:35000")
    return MlflowClient()


@pytest.fixture
def dioptra_client():
    return TestDioptraClient()


@pytest.fixture
def docker_client():
    c = docker.client.from_env()
    yield c
    c.close()


@pytest.fixture
def mnist_data_dir(tmp_path_factory):
    mnist_data_dir = tmp_path_factory.mktemp("mnist_data_dir")

    try:
        download_data(
            [
                "--cache-dir",
                f"{DIOPTRA_CACHE_DIR / 'mnist'}",
                "--data-dir",
                str(mnist_data_dir),
            ]
        )

    except SystemExit as e:
        if e.code != 0:
            raise e

    return str(mnist_data_dir)
