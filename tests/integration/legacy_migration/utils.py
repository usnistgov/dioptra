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
import subprocess
import boto3
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from testinfra.host import Host

PathLike = Union[str, Path]


@dataclass
class TestbedHosts(object):
    minio: Host
    mlflow_tracking: Host
    nginx: Host
    redis: Host
    restapi: Host
    tfcpu_01: Host


def initialize_testbed_rest_api(testbed_client, custom_plugins_evaluation_tar_gz):
    # Create experiment namespace
    response_experiment = testbed_client.get_experiment_by_name(name="mnist")

    if response_experiment is None or "Not Found" in response_experiment.get(
        "message", []
    ):
        response_experiment = testbed_client.register_experiment(name="mnist")

    # Register Tensorflow (CPU) worker queue
    response_queue = testbed_client.get_queue_by_name(name="tensorflow_cpu")

    if response_queue is None or "Not Found" in response_queue.get("message", []):
        response_queue = testbed_client.register_queue(name="tensorflow_cpu")

    # Register the evaluation custom plugin
    response_custom_plugins = testbed_client.get_custom_task_plugin(name="evaluation")

    if response_custom_plugins is None or "Not Found" in response_custom_plugins.get(
        "message", []
    ):
        response_custom_plugins = testbed_client.upload_custom_plugin_package(
            custom_plugin_name="evaluation",
            custom_plugin_file=str(custom_plugins_evaluation_tar_gz),
        )


def mlflow_run_id_is_not_known(response):
    return (response["mlflowRunId"] is None) and (
        response["status"] not in set(("failed", "finished"))
    )


def job_still_running(response):
    return response["status"] not in set(("failed", "finished"))


def run_train_entrypoint_job(testbed_client, workflows_tar_gz):
    response_shallow_train = testbed_client.submit_job(
        workflows_file=str(workflows_tar_gz),
        experiment_name="mnist",
        entry_point="train",
        entry_point_kwargs=" ".join(
            [
                "-P model_architecture=shallow_net",
                "-P epochs=5",
                "-P register_model_name=mnist_shallow_net",
            ]
        ),
    )

    while job_still_running(response_shallow_train):
        time.sleep(1)
        response_shallow_train = testbed_client.get_job_by_id(
            response_shallow_train["jobId"]
        )

    return response_shallow_train

def connect_to_minio_server(
    minio_endpoint_url: str,
    minio_root_user: str,
    minio_root_password: str,
    ):
    os.environ["NODE_TLS_REJECT_UNAUTHORIZED"] = "0"
    # Attempt to connect to minio server with boto3.
    s3_resource = boto3.resource(
        "s3",
        endpoint_url=minio_endpoint_url,
        aws_access_key_id=minio_root_user,
        aws_secret_access_key=minio_root_password,
    )
    return s3_resource

def sync_from_minio_bucket(
    compose_file: PathLike,
    minio_endpoint_alias: str,
    minio_root_user: str,
    minio_root_password: str,
    bucket: str,
    dest_dir: str,
) -> None:
    subprocess.check_call(
        f'docker-compose -f {compose_file} run --rm mc -c "'
        f"mc alias set {minio_endpoint_alias} http://minio:9000 "
        f"{minio_root_user} {minio_root_password} && mc mirror --overwrite "
        f"--remove {minio_endpoint_alias}/{bucket} {dest_dir}"
        '"',
        shell=True,
    )


def sync_to_minio_bucket(
    compose_file: PathLike,
    minio_endpoint_alias: str,
    minio_root_user: str,
    minio_root_password: str,
    bucket: str,
    src_dir: str,
) -> None:
    subprocess.check_call(
        f'docker-compose -f {compose_file} run --rm mc -c "'
        f"mc alias set {minio_endpoint_alias} http://minio:9000 "
        f"{minio_root_user} {minio_root_password} && mc mirror --overwrite "
        f"--remove {src_dir} {minio_endpoint_alias}/{bucket}"
        '"',
        shell=True,
    )


def download_minio_bucket_data(
    compose_file: PathLike, minio_bucket_data_dir: str, target_dir: str
) -> None:
    subprocess.check_call(
        f"docker-compose -f {compose_file} up -d minio-bucket-data-helper && "
        f"docker cp minio-bucket-data-helper:/minio-bucket-data/{target_dir} "
        f"{minio_bucket_data_dir}/{target_dir} && "
        f"docker-compose -f {compose_file} down",
        shell=True,
    )


def upload_minio_bucket_data(
    compose_file: PathLike, minio_bucket_data_dir: str, target_dir: str
) -> None:
    subprocess.check_call(
        f"docker-compose -f {compose_file} up -d minio-bucket-data-helper && "
        f"docker cp {minio_bucket_data_dir}/{target_dir} "
        f"minio-bucket-data-helper:/minio-bucket-data/{target_dir} && "
        f"docker-compose -f {compose_file} down",
        shell=True,
    )
