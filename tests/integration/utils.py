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
import time
from pathlib import Path
from posixpath import join as urljoin
from typing import List, Optional, Union
from urllib.parse import urlparse, urlunparse

import requests
from docker.client import DockerClient

from tests.utils import Timer

PathLike = Union[str, Path]


class TestbedAPIClient(object):
    def __init__(self, address: str = "http://localhost:30080") -> None:
        address = f"{address}/api"
        self._scheme, self._netloc, self._path, _, _, _ = urlparse(address)

    @property
    def experiment_endpoint(self) -> str:
        return urlunparse(
            (self._scheme, self._netloc, urljoin(self._path, "experiment/"), "", "", "")
        )

    @property
    def job_endpoint(self) -> str:
        return urlunparse(
            (self._scheme, self._netloc, urljoin(self._path, "job/"), "", "", "")
        )

    @property
    def task_plugin_endpoint(self) -> str:
        return urlunparse(
            (self._scheme, self._netloc, urljoin(self._path, "taskPlugin/"), "", "", "")
        )

    @property
    def task_plugin_builtins_endpoint(self) -> str:
        return urlunparse(
            (
                self._scheme,
                self._netloc,
                urljoin(self._path, "taskPlugin/securingai_builtins"),
                "",
                "",
                "",
            )
        )

    @property
    def task_plugin_custom_endpoint(self) -> str:
        return urlunparse(
            (
                self._scheme,
                self._netloc,
                urljoin(self._path, "taskPlugin/securingai_custom"),
                "",
                "",
                "",
            )
        )

    @property
    def queue_endpoint(self) -> str:
        return urlunparse(
            (self._scheme, self._netloc, urljoin(self._path, "queue/"), "", "", "")
        )

    def delete_custom_task_plugin(self, name: str):
        plugin_name_query: str = urljoin(self.task_plugin_custom_endpoint, name)
        return requests.delete(plugin_name_query).json()

    def get_experiment_by_id(self, id: int):
        experiment_id_query: str = urljoin(self.experiment_endpoint, str(id))
        return requests.get(experiment_id_query).json()

    def get_experiment_by_name(self, name: str):
        experiment_name_query: str = urljoin(self.experiment_endpoint, "name", name)
        return requests.get(experiment_name_query).json()

    def get_job_by_id(self, id: str):
        job_id_query: str = urljoin(self.job_endpoint, id)
        return requests.get(job_id_query).json()

    def get_queue_by_id(self, id: int):
        queue_id_query: str = urljoin(self.queue_endpoint, str(id))
        return requests.get(queue_id_query).json()

    def get_queue_by_name(self, name: str):
        queue_name_query: str = urljoin(self.queue_endpoint, "name", name)
        return requests.get(queue_name_query).json()

    def get_builtin_task_plugin(self, name: str):
        task_plugin_name_query: str = urljoin(self.task_plugin_builtins_endpoint, name)
        return requests.get(task_plugin_name_query).json()

    def get_custom_task_plugin(self, name: str):
        task_plugin_name_query: str = urljoin(self.task_plugin_custom_endpoint, name)
        return requests.get(task_plugin_name_query).json()

    def list_experiments(self):
        return requests.get(self.experiment_endpoint).json()

    def list_jobs(self):
        return requests.get(self.job_endpoint).json()

    def list_queues(self):
        return requests.get(self.queue_endpoint).json()

    def list_all_task_plugins(self):
        return requests.get(self.task_plugin_endpoint).json()

    def list_builtin_task_plugins(self):
        return requests.get(self.task_plugin_builtins_endpoint).json()

    def list_custom_task_plugins(self):
        return requests.get(self.task_plugin_custom_endpoint).json()

    def lock_queue(self, name: str):
        queue_name_query: str = urljoin(self.queue_endpoint, "name", name, "lock")
        return requests.put(queue_name_query).json()

    def unlock_queue(self, name: str):
        queue_name_query: str = urljoin(self.queue_endpoint, "name", name, "lock")
        return requests.delete(queue_name_query).json()

    def register_experiment(self, name: str):
        experiment_registration_form = {"name": name}

        response = requests.post(
            self.experiment_endpoint,
            data=experiment_registration_form,
        )

        return response.json()

    def register_queue(self, name: str = "tensorflow_cpu"):
        queue_registration_form = {"name": name}

        response = requests.post(
            self.queue_endpoint,
            data=queue_registration_form,
        )

        return response.json()

    def submit_job(
        self,
        workflows_file: PathLike,
        experiment_name: str,
        entry_point: str,
        entry_point_kwargs: Optional[str] = None,
        depends_on: Optional[str] = None,
        queue: str = "tensorflow_cpu",
        timeout: str = "24h",
    ):
        job_form = {
            "experiment_name": experiment_name,
            "queue": queue,
            "timeout": timeout,
            "entry_point": entry_point,
        }

        if entry_point_kwargs is not None:
            job_form["entry_point_kwargs"] = entry_point_kwargs

        if depends_on is not None:
            job_form["depends_on"] = depends_on

        workflows_file = Path(workflows_file)

        with workflows_file.open("rb") as f:
            job_files = {"workflow": (workflows_file.name, f)}
            response = requests.post(
                self.job_endpoint,
                data=job_form,
                files=job_files,
            )

        return response.json()

    def upload_custom_plugin_package(
        self,
        custom_plugin_name: str,
        custom_plugin_file: PathLike,
        collection: str = "securingai_custom",
    ):
        plugin_upload_form = {
            "task_plugin_name": custom_plugin_name,
            "collection": collection,
        }

        custom_plugin_file = Path(custom_plugin_file)

        with custom_plugin_file.open("rb") as f:
            request_files = {"task_plugin_file": (custom_plugin_file.name, f)}
            response = requests.post(
                self.task_plugin_endpoint,
                data=plugin_upload_form,
                files=request_files,
            )

        return response.json()


def destroy_volumes(client: DockerClient, prefix: str) -> None:
    volumes = [v for v in client.volumes.list() if v.name.startswith(prefix)]

    for v in volumes:
        v.remove()


def initialize_minio(
    compose_file: PathLike,
    minio_endpoint_alias: str,
    minio_root_user: str,
    minio_root_password: str,
    plugins_builtins_dir: str,
) -> None:
    subprocess.check_call(
        f'docker-compose -f {compose_file} run --rm mc -c "'
        f"mc alias set {minio_endpoint_alias} http://minio:9000 "
        f"{minio_root_user} {minio_root_password} && mc mb "
        f"{minio_endpoint_alias}/plugins {minio_endpoint_alias}/workflow && "
        f"mc mirror --overwrite --remove /task-plugins/{plugins_builtins_dir}/ "
        f"{minio_endpoint_alias}/plugins/{plugins_builtins_dir}"
        '"',
        shell=True,
    )


def upload_mnist_images(
    compose_file: PathLike, mnist_data_dir: str, dest_dir: str
) -> None:
    subprocess.check_call(
        f"docker-compose -f {compose_file} up -d mnist-data-helper && "
        f"docker cp {mnist_data_dir}/training mnist-data-helper:{dest_dir}/training && "
        f"docker cp {mnist_data_dir}/testing mnist-data-helper:{dest_dir}/testing && "
        f"docker-compose -f {compose_file} down",
        shell=True,
    )


def print_docker_logs(compose_file: PathLike) -> None:
    subprocess.check_call(
        [
            "docker-compose",
            "-f",
            f"{compose_file}",
            "logs",
        ]
    )


def run_docker_service(
    compose_file: PathLike, service: str, remove: bool = True
) -> None:
    args: List[str] = [
        "docker-compose",
        "-f",
        f"{compose_file}",
        "run",
    ]

    if remove:
        args.append("--rm")

    args.append(service)

    subprocess.check_call(args)


def start_docker_services(compose_file: PathLike, services: List[str]) -> None:
    subprocess.check_call(
        [
            "docker-compose",
            "-f",
            f"{compose_file}",
            "up",
            "-d",
        ]
        + services
    )


def stop_docker_services(compose_file: PathLike) -> None:
    subprocess.check_call(
        [
            "docker-compose",
            "-f",
            f"{compose_file}",
            "down",
        ]
    )


def wait_for_healthy_status(
    docker_client: DockerClient, container_names: List[str], timeout: float = 300.0
) -> None:
    with Timer(timeout=timeout) as timer:
        for name in container_names:
            health_status: str = (
                docker_client.containers.get(name)
                .attrs.get("State")
                .get("Health")
                .get("Status")
                .strip()
                .lower()
            )

            while health_status != "healthy":
                if docker_client.containers.get(name).status != "running":
                    raise RuntimeError(
                        f"The {name} service has a status of "
                        f"{docker_client.containers.get(name).status} and is no "
                        "longer running."
                    )

                if health_status == "unhealthy":
                    raise RuntimeError(f"The {name} service is unhealthy.")

                if timer.timeout_exceeded:
                    raise TimeoutError(f"The {name} service timed out.")

                time.sleep(1)

                health_status = (
                    docker_client.containers.get(name)
                    .attrs.get("State")
                    .get("Health")
                    .get("Status")
                    .strip()
                    .lower()
                )
