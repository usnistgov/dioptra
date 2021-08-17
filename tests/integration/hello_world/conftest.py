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
import tarfile
from pathlib import Path
from subprocess import CalledProcessError

import pytest
import testinfra

from tests.integration.hello_world.utils import TestbedHosts
from tests.integration.utils import (
    destroy_volumes,
    initialize_minio,
    print_docker_logs,
    run_docker_service,
    start_docker_services,
    stop_docker_services,
    wait_for_healthy_status,
)

CONFTEST_DIR = Path(__file__).absolute().parent
WORKFLOWS_DIR = CONFTEST_DIR / "workflows"
MINIO_ENDPOINT_ALIAS = "minio"
MINIO_ROOT_USER = "minio"
MINIO_ROOT_PASSWORD = "minio123"
PLUGINS_BUILTINS_DIR = "securingai_builtins"


@pytest.fixture
def workflows_tar_gz(tmp_path_factory):
    hello_world_dir = tmp_path_factory.mktemp("hello_world")

    workflows_tar_gz_path: Path = hello_world_dir / "workflows.tar.gz"

    with tarfile.open(name=str(workflows_tar_gz_path), mode="w:gz") as f:
        for datafile in (WORKFLOWS_DIR / "MLproject", WORKFLOWS_DIR / "hello_world.py"):
            with datafile.open(mode="rb") as f_data:
                tarinfo = tarfile.TarInfo(name=datafile.name)
                tarinfo.size = len(f_data.read())
                f_data.seek(0)
                f.addfile(tarinfo=tarinfo, fileobj=f_data)

    yield workflows_tar_gz_path


@pytest.fixture
def testbed_hosts(request, docker_client):
    # Declare path to docker-compose.yml file
    docker_compose_file: Path = CONFTEST_DIR / "docker-compose.yml"

    # Stop any containers and remove any volumes from previous integration tests
    stop_docker_services(compose_file=docker_compose_file)
    destroy_volumes(client=docker_client, prefix="hello_world_")

    try:
        # Start and initialize the Minio service
        start_docker_services(compose_file=docker_compose_file, services=["minio"])
        wait_for_healthy_status(docker_client=docker_client, container_names=["minio"])
        initialize_minio(
            compose_file=docker_compose_file,
            minio_endpoint_alias=MINIO_ENDPOINT_ALIAS,
            minio_root_user=MINIO_ROOT_USER,
            minio_root_password=MINIO_ROOT_PASSWORD,
            plugins_builtins_dir=PLUGINS_BUILTINS_DIR,
        )

        # Initialize REST API database
        run_docker_service(
            compose_file=docker_compose_file, service="restapi-db-upgrade"
        )

        # Start the docker-compose stack for integration testing
        start_docker_services(
            compose_file=docker_compose_file,
            services=[
                "minio",
                "mlflow-tracking",
                "nginx",
                "redis",
                "restapi",
                "tfcpu-01",
            ],
        )
        wait_for_healthy_status(
            docker_client=docker_client,
            container_names=[
                "minio",
                "mlflow-tracking",
                "redis",
                "restapi",
                "nginx",
            ],
        )

        # return host connection to each service
        yield TestbedHosts(
            minio=testinfra.get_host("docker://minio"),
            mlflow_tracking=testinfra.get_host("docker://mlflow-tracking"),
            nginx=testinfra.get_host("docker://nginx"),
            redis=testinfra.get_host("docker://redis"),
            restapi=testinfra.get_host("docker://restapi"),
            tfcpu_01=testinfra.get_host("docker://tfcpu-01"),
        )

    except (RuntimeError, TimeoutError, CalledProcessError):
        raise

    finally:
        # Teardown
        print_docker_logs(compose_file=docker_compose_file)
        stop_docker_services(compose_file=docker_compose_file)
        destroy_volumes(client=docker_client, prefix="hello_world_")
