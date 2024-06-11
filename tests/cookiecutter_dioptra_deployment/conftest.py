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
import pytest


@pytest.fixture
def context():
    return {
        "deployment_name": "Dioptra deployment",
        "__project_slug": "dioptra-deployment",
        "container_registry": "",
        "__container_namespace": "dioptra",
        "container_tag": "dev",
        "docker_compose_path": "/usr/local/bin/docker-compose",
        "systemd_required_mounts": "",
        "nginx_server_name": "dioptra.example.org",
        "nginx_expose_ports_on_localhost_only": "True",
        "postgres_container_tag": "15",
        "__restapi_http_port": "80",
        "__restapi_https_port": "443",
        "__db_admin_username": "postgres",
        "__db_admin_database": "postgres",
        "pgadmin_default_email": "dioptra@example.com",
        "num_tensorflow_cpu_workers": "1",
        "num_tensorflow_gpu_workers": "0",
        "num_pytorch_cpu_workers": "1",
        "num_pytorch_gpu_workers": "0",
        "__containers": {
            "networks": ["dioptra"],
            "nginx": {
                "image": "nginx",
                "namespace": "dioptra",
                "tag": "dev",
                "registry": "",
            },
            "mlflow_tracking": {
                "image": "mlflow-tracking",
                "namespace": "dioptra",
                "tag": "dev",
                "registry": "",
            },
            "restapi": {
                "image": "restapi",
                "namespace": "dioptra",
                "tag": "dev",
                "registry": "",
            },
            "tfcpu": {
                "image": "tensorflow2-cpu",
                "namespace": "dioptra",
                "tag": "dev",
                "registry": "",
            },
            "tfgpu": {
                "image": "tensorflow2-gpu",
                "namespace": "dioptra",
                "tag": "dev",
                "registry": "",
            },
            "pytorchcpu": {
                "image": "pytorch-cpu",
                "namespace": "dioptra",
                "tag": "dev",
                "registry": "",
            },
            "pytorchgpu": {
                "image": "pytorch-gpu",
                "namespace": "dioptra",
                "tag": "dev",
                "registry": "",
            },
            "argbash": {
                "image": "argbash",
                "namespace": "matejak",
                "tag": "latest",
                "registry": "",
            },
            "db": {
                "image": "postgres",
                "namespace": "",
                "tag": "{{ cookiecutter.postgres_container_tag }}",
                "registry": "",
            },
            "dbadmin": {
                "image": "pgadmin4",
                "namespace": "dpage",
                "tag": "latest",
                "registry": "",
            },
            "mc": {
                "image": "mc",
                "namespace": "minio",
                "tag": "latest",
                "registry": "",
            },
            "minio": {
                "image": "minio",
                "namespace": "minio",
                "tag": "latest",
                "registry": "",
            },
            "nodejs": {
                "image": "node",
                "namespace": "",
                "tag": "latest",
                "registry": "",
            },
            "redis": {
                "image": "redis",
                "namespace": "",
                "tag": "latest",
                "registry": "",
            },
        },
        "_is_pytest": "True",
    }


@pytest.fixture
def result(cookies, context):
    return cookies.bake(extra_context={**context})
