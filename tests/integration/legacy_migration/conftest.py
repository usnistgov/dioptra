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

from tests.integration.legacy_migration.migrate_s3 import migrate_s3
from tests.integration.legacy_migration.utils import (
    TestbedHosts,
    download_minio_bucket_data,
    initialize_testbed_rest_api,
    run_train_entrypoint_job,
    sync_from_minio_bucket,
    sync_to_minio_bucket,
    upload_minio_bucket_data,
)
from tests.integration.utils import (
    destroy_volumes,
    initialize_minio,
    print_docker_logs,
    run_docker_service,
    start_docker_services,
    stop_docker_services,
    upload_mnist_images,
    wait_for_healthy_status,
)

CONFTEST_DIR = Path(__file__).absolute().parent
WORKFLOWS_DIR = CONFTEST_DIR / "workflows"
CUSTOM_PLUGINS_EVALUATION_DIR = (
    CONFTEST_DIR / "task_plugins" / "securingai_custom" / "evaluation"
)
MINIO_ENDPOINT_ALIAS = "minio"
MINIO_ROOT_USER = "minio"
MINIO_ROOT_PASSWORD = "minio123"
PLUGINS_BUILTINS_DIR = "securingai_builtins"


@pytest.fixture
def custom_plugins_evaluation_tar_gz(tmp_path_factory):
    custom_plugins_evaluation_tar_gz_dir = tmp_path_factory.mktemp(
        "tf_mnist_classifier_custom_plugins_evaluation"
    )
    custom_plugins_evaluation_tar_gz_path: Path = (
        custom_plugins_evaluation_tar_gz_dir / "custom-plugins-evaluation.tar.gz"
    )

    with tarfile.open(
        name=str(custom_plugins_evaluation_tar_gz_path), mode="w:gz"
    ) as f:
        for datafile in (
            CUSTOM_PLUGINS_EVALUATION_DIR / "__init__.py",
            CUSTOM_PLUGINS_EVALUATION_DIR / "import_keras.py",
            CUSTOM_PLUGINS_EVALUATION_DIR / "tensorflow.py",
        ):
            with datafile.open(mode="rb") as f_data:
                tarinfo = tarfile.TarInfo(name=f"evaluation/{datafile.name}")
                tarinfo.size = len(f_data.read())
                f_data.seek(0)
                f.addfile(tarinfo=tarinfo, fileobj=f_data)

    yield custom_plugins_evaluation_tar_gz_path


@pytest.fixture
def workflows_tar_gz(tmp_path_factory):
    workflows_tar_gz_dir = tmp_path_factory.mktemp("tf_mnist_classifier_workflows")

    workflows_tar_gz_path: Path = workflows_tar_gz_dir / "workflows.tar.gz"

    with tarfile.open(name=str(workflows_tar_gz_path), mode="w:gz") as f:
        for datafile in (
            WORKFLOWS_DIR / "MLproject",
            WORKFLOWS_DIR / "train.py",
            WORKFLOWS_DIR / "fgm.py",
            WORKFLOWS_DIR / "infer.py",
        ):
            with datafile.open(mode="rb") as f_data:
                tarinfo = tarfile.TarInfo(name=datafile.name)
                tarinfo.size = len(f_data.read())
                f_data.seek(0)
                f.addfile(tarinfo=tarinfo, fileobj=f_data)

    yield workflows_tar_gz_path


@pytest.fixture
def train_entrypoint_response(
    request,
    mnist_data_dir,
    docker_client,
    testbed_client,
    custom_plugins_evaluation_tar_gz,
    workflows_tar_gz,
):
    # Declare path to docker-compose.yml file
    legacy_docker_compose_file: Path = CONFTEST_DIR / "docker-compose.legacy.yml"

    # Stop any containers and remove any volumes from previous integration tests
    stop_docker_services(compose_file=legacy_docker_compose_file)
    destroy_volumes(client=docker_client, prefix="legacy_migration_")

    try:
        # Copy MNIST images into Docker volume
        upload_mnist_images(
            compose_file=legacy_docker_compose_file,
            mnist_data_dir=str(mnist_data_dir),
            dest_dir="/nfs/data",
        )

        # Start and initialize the Minio service
        start_docker_services(
            compose_file=legacy_docker_compose_file, services=["minio"]
        )
        wait_for_healthy_status(docker_client=docker_client, container_names=["minio"])
        initialize_minio(
            compose_file=legacy_docker_compose_file,
            minio_endpoint_alias=MINIO_ENDPOINT_ALIAS,
            minio_root_user=MINIO_ROOT_USER,
            minio_root_password=MINIO_ROOT_PASSWORD,
            plugins_builtins_dir=PLUGINS_BUILTINS_DIR,
        )

        # Initialize REST API database
        run_docker_service(
            compose_file=legacy_docker_compose_file, service="restapi-db-upgrade"
        )

        # Start the legacy docker-compose stack
        start_docker_services(
            compose_file=legacy_docker_compose_file,
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

        # Register experiment namespace, worker queue, and upload custom task plugins
        # via the Testbed REST API
        initialize_testbed_rest_api(
            testbed_client=testbed_client,
            custom_plugins_evaluation_tar_gz=custom_plugins_evaluation_tar_gz,
        )

        # Run train entrypoint job
        response_shallow_train = run_train_entrypoint_job(
            testbed_client=testbed_client, workflows_tar_gz=workflows_tar_gz
        )

    except (RuntimeError, TimeoutError, CalledProcessError):
        raise

    finally:
        # Teardown
        # print_docker_logs(compose_file=legacy_docker_compose_file)
        stop_docker_services(compose_file=legacy_docker_compose_file)

    return response_shallow_train


@pytest.fixture
def migrate_s3_files(
    docker_client,
    train_entrypoint_response,
    tmp_path_factory,
):
    minio_bucket_data_dir = tmp_path_factory.mktemp("minio_bucket_data", numbered=False)

    # Declare path to docker-compose.yml file
    docker_compose_file: Path = CONFTEST_DIR / "docker-compose.yml"

    # Stop any containers from previous integration tests
    stop_docker_services(compose_file=docker_compose_file)

    try:
        # Upgrade the MLFlow Tracking database
        run_docker_service(
            compose_file=docker_compose_file, service="mlflow-tracking-db-upgrade"
        )

        # Sync Minio Bucket Data to Temporary Dir
        sync_from_minio_bucket(
            compose_file=docker_compose_file,
            minio_endpoint_alias=MINIO_ENDPOINT_ALIAS,
            minio_root_user=MINIO_ROOT_USER,
            minio_root_password=MINIO_ROOT_PASSWORD,
            bucket="mlflow-tracking",
            dest_dir="/minio-bucket-data/old",
        )
        download_minio_bucket_data(
            compose_file=docker_compose_file,
            minio_bucket_data_dir=str(minio_bucket_data_dir),
            target_dir="old",
        )

        # Migration Script
        migrate_s3(minio_bucket_data_dir)

        # Sync Temporary Dir
        upload_minio_bucket_data(
            compose_file=docker_compose_file,
            minio_bucket_data_dir=str(minio_bucket_data_dir),
            target_dir="new",
        )
        sync_to_minio_bucket(
            compose_file=docker_compose_file,
            minio_endpoint_alias=MINIO_ENDPOINT_ALIAS,
            minio_root_user=MINIO_ROOT_USER,
            minio_root_password=MINIO_ROOT_PASSWORD,
            bucket="mlflow-tracking",
            src_dir="/minio-bucket-data/new",
        )

    except (RuntimeError, TimeoutError, CalledProcessError):
        raise

    finally:
        # Teardown
        print_docker_logs(compose_file=docker_compose_file)
        stop_docker_services(compose_file=docker_compose_file)


@pytest.fixture
def testbed_hosts(
    docker_client,
    migrate_s3_files,
):
    # Declare path to docker-compose.yml file
    docker_compose_file: Path = CONFTEST_DIR / "docker-compose.yml"

    # Stop any containers from previous integration tests
    stop_docker_services(compose_file=docker_compose_file)

    try:
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
        destroy_volumes(client=docker_client, prefix="legacy_migration_")
