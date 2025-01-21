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

import json
import os
import pytest
import shutil
import subprocess
import yaml

TEMPLATE_REPO = 'https://github.com/usnistgov/dioptra'
BRANCH = "dev"
TEST_DIR = "test_cruft_deploy"
EXPECTED_DEFAULTS = {
    # DONE
    #check the deployment folder name
    "deployment_name": "dioptra-deployment", # slugified deployment name

    #maybe check images in docker-compose?
    # DONE
    "container_tag": "dev",

    "docker_compose_path": "docker compose",

    #check deployment/config/nginx/http(s)_ dbadmin.conf, minio.conf, mlflow.conf, restapi
    "nginx_server_name": "dioptra.example.org",

    #check docker-compose.yml?
    "nginx_expose_ports_on_localhost_only": "True",

    #check deployment/docker-compose.init.yml db: image: postgres:#
    "postgres_container_tag": "15",

    # DONE
    #check deployment/envs/dioptra-deployment-dbadmin.env
    "pgadmin_default_email": "dioptra@example.com",

    #check deployment/docker-compose.yml for number of named containers
    "num_tensorflow_cpu_workers": "1",
    "num_tensorflow_gpu_workers": "0",
    "num_pytorch_cpu_workers": "1",
    "num_pytorch_gpu_workers": "0",
}

@pytest.fixture(scope='session')
def rendered_folder():
    """Set up the test dir and run cruft create"""
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR)

    cruft_command = ['cruft', 'create', TEMPLATE_REPO, 
                     '--checkout', BRANCH,
                     '--directory', 
                     'cookiecutter-templates/cookiecutter-dioptra-deployment',
                     '--no-input'
                     ]
    
    try:
        subprocess.run(cruft_command, cwd=TEST_DIR, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Cruft command failed: {e}")
        assert False

    rendered_folders = os.listdir(TEST_DIR)
    assert len(rendered_folders) == 1, 'The wrong number of deployment folders was generated.'
    return os.path.join(TEST_DIR, rendered_folders[0])


def test_deployment_name(rendered_folder):
    deployment_folder_name = os.path.basename(rendered_folder)
    assert deployment_folder_name == EXPECTED_DEFAULTS['deployment_name'], (
        f'Deployment folder name mismatch. '
        f'Expected "{EXPECTED_DEFAULTS["deployment_name"]}", Got: "{deployment_folder_name}"'
    )


def test_dioptra_container_tags(rendered_folder):
    """Test that the Dioptra containers have the right tag."""
    expected_tag = EXPECTED_DEFAULTS["container_tag"]
    dioptra_prefix = "dioptra/"
    docker_compose_file = os.path.join(rendered_folder, "docker-compose.yml")

    assert os.path.exists(docker_compose_file), f"File not found: {docker_compose_file}"

    with open(docker_compose_file, "r") as compose_file:
        compose_data = yaml.safe_load(compose_file)

    for service_name, service_details in compose_data.get("services", {}).items():
        image = service_details.get("image", "")
        if image.startswith(dioptra_prefix):
            provider, service, tag = image.partition(":")
            assert tag == expected_tag, (
                f"Service '{service_name}' has incorrect tag. "
                f"Expected: '{expected_tag}', Found: '{tag}'"
            )


def test_pgadmin_default_email(rendered_folder):
    env_file_path = os.path.join(rendered_folder, "envs", 
                                 f"{EXPECTED_DEFAULTS['deployment_name']}-dbadmin.env")
    
    assert os.path.exists(env_file_path), f"File not found: {env_file_path}"
    with open (env_file_path, "r") as env_file:
        content = env_file.read()
        expected_line = f"PGADMIN_DEFAULT_EMAIL={EXPECTED_DEFAULTS['pgadmin_default_email']}"
        assert expected_line in content, (
            f"Expected line not found in {env_file_path}. "
            f"Expected: '{expected_line}"
        )


def test_postgres_container_tag(rendered_folder):
    """Test that the postgres container has the right tag."""
    expected_tag = EXPECTED_DEFAULTS["postgres_container_tag"]

    docker_compose_file = os.path.join(rendered_folder, "docker-compose.yml")
    assert os.path.exists(docker_compose_file), f"File not found: {docker_compose_file}"

    with open(docker_compose_file, "r") as compose_file:
        compose_data = yaml.safe_load(compose_file)

    postgres_service = compose_data.get("services", {}).get("dioptra-deployment-db", {})
    image = postgres_service.get("image", "")
    assert image.endswith(f":{expected_tag}"), (
        f"Service '{image}' has incorrect tag. "
        f"Expected: '{expected_tag}'" 
    )