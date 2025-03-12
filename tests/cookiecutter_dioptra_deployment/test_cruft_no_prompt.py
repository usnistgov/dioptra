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
import re
import shutil
import subprocess

import pytest
import yaml

TEMPLATE_REPO = "https://github.com/usnistgov/dioptra"
BRANCH = "dev"
TEST_DIR = "test_cruft_deploy"

# Based on cookiecutter.json
EXPECTED_DEFAULTS = {
    "deployment_name": "dioptra-deployment",  # slugified deployment name
    "container_tag": "dev",
    "docker_compose_path": "docker compose",
    "nginx_server_name": "dioptra.example.org",
    "nginx_expose_ports_on_localhost_only": "True",
    "postgres_container_tag": "15",
    "pgadmin_default_email": "dioptra@example.com",
    "num_tensorflow_cpu_workers": "1",
    "num_tensorflow_gpu_workers": "0",
    "num_pytorch_cpu_workers": "1",
    "num_pytorch_gpu_workers": "0",
}


@pytest.fixture(scope="session")
def rendered_folder():
    """Set up the test dir and run cruft create"""
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR)

    cruft_command = [
        "cruft",
        "create",
        TEMPLATE_REPO,
        "--checkout",
        BRANCH,
        "--directory",
        "cookiecutter-templates/cookiecutter-dioptra-deployment",
        "--no-input",
    ]

    try:
        subprocess.run(cruft_command, cwd=TEST_DIR, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Cruft command failed: {e}")
        assert False

    rendered_folders = os.listdir(TEST_DIR)
    assert (
        len(rendered_folders) == 1
    ), "The wrong number of deployment folders was generated."

    rendered_path = os.path.join(TEST_DIR, rendered_folders[0])
    yield rendered_path

    # Clean up after tests run
    shutil.rmtree(TEST_DIR)


def test_deployment_name(rendered_folder):
    deployment_folder_name = os.path.basename(rendered_folder)
    assert deployment_folder_name == EXPECTED_DEFAULTS["deployment_name"], (
        f"Deployment folder name mismatch. "
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


def test_docker_compose_path(rendered_folder):
    """Test that the docker compose path was correctly set in init-deployment.sh"""
    script_name = "init-deployment.sh"
    script_path = os.path.join(rendered_folder, script_name)
    expected_value = EXPECTED_DEFAULTS["docker_compose_path"]

    assert os.path.exists(script_path), f"{script_name} not found at: {script_path}"

    with open(script_path, "r") as script_file:
        script_content = script_file.read()

    # Ensure cookiecutter placeholder value no longer exists
    placeholder_value = " {{ cookiecutter.docker_compose_path }} "
    assert (
        placeholder_value not in script_content
    ), f"Placeholder {placeholder_value} should not be in {script_path}"

    # Get the docker_compose() function contents
    compose_function_pattern = r"^docker_compose\(\) \{.*?^\}$"
    match = re.search(
        compose_function_pattern, script_content, re.DOTALL | re.MULTILINE
    )
    assert match, f"docker_compose() function not found in {script_path}"
    function_content = match.group()

    # Expected lines in the init-deployment.sh docker_compose() function
    expected_usage_1 = f"  if ! {expected_value} " + '"${@}"; then'
    expected_usage_2 = f'      "{expected_value}, exiting..."'

    assert (
        expected_usage_1 in function_content
    ), f"Expected usage '{expected_usage_1} not found in docker_compose () function."

    assert (
        expected_usage_2 in function_content
    ), f"Expected usage '{expected_usage_2} not found in docker_compose () function."


def test_nginx_expose_ports_on_localhost_only(rendered_folder):
    """Test that the nginx service container's ports are assigned correctly."""
    # expected_prefix assuming nginx_expose_ports_on_localhost_only = True
    expected_prefix = "127.0.0.1:"
    compose_file_path = os.path.join(rendered_folder, "docker-compose.yml")
    assert os.path.exists(compose_file_path), f"{compose_file_path} not found."

    with open(compose_file_path, "r") as compose_file:
        compose_content = yaml.safe_load(compose_file)

    # Find the nginx service name in the docker compose services, otherwise None
    nginx_service_name = next(
        (
            service_name
            for service_name in compose_content.get("services", {})
            if service_name.endswith("nginx")
        ),
        None,
    )
    assert (
        nginx_service_name
    ), f"No service found with a name ending in 'nginx' in {compose_file_path}."

    nginx_service = compose_content["services"][nginx_service_name]
    assert nginx_service, f"Nginx service not found in {compose_file_path}"

    ports = nginx_service.get("ports", [])
    assert ports, f"No ports defined for the Nginx service in {compose_file_path}"

    for port in ports:
        assert port.startswith(
            expected_prefix
        ), f"Port '{port}' does not start with '{expected_prefix}'."


def test_nginx_server_name(rendered_folder):
    """Test that the nginx server name propogates to the conf files"""
    nginx_config_dir = os.path.join(rendered_folder, "config", "nginx")
    expected_name = EXPECTED_DEFAULTS["nginx_server_name"]
    conf_files = [
        "http_dbadmin.conf",
        "http_minio.conf",
        "http_mlflow.conf",
        "http_restapi.conf",
        "https_dbadmin.conf",
        "https_minio.conf",
        "https_mlflow.conf",
        "https_restapi.conf",
    ]

    assert os.path.exists(
        nginx_config_dir
    ), f"Nginx config directory not found: {nginx_config_dir}"

    for conf_file in conf_files:
        conf_path = os.path.join(nginx_config_dir, conf_file)
        assert os.path.exists(conf_path), f"'{conf_file}' does not exist"

        with open(conf_path, "r") as file:
            conf_content = file.read()

        # Some files have multiple server blocks, get them all
        server_blocks = re.findall(r"server\s*{.*?}", conf_content, re.DOTALL)
        assert server_blocks, f"No 'server' blocks found in {conf_file}"

        for server_block in server_blocks:
            server_name_search = re.search(r"server_name\s+(.+?);", server_block)
            assert (
                server_name_search
            ), f"Server block without 'server_name' found in {conf_file}"

            found_server_name = server_name_search.group(1).strip()
            assert found_server_name == expected_name, (
                f"Expected server_name '{expected_name}' but found "
                f"'{found_server_name}' in {conf_file}"
            )


def test_pgadmin_default_email(rendered_folder):
    env_file_path = os.path.join(
        rendered_folder, "envs", f"{EXPECTED_DEFAULTS['deployment_name']}-dbadmin.env"
    )

    assert os.path.exists(env_file_path), f"File not found: {env_file_path}"
    with open(env_file_path, "r") as env_file:
        content = env_file.read()
        expected_line = (
            f"PGADMIN_DEFAULT_EMAIL={EXPECTED_DEFAULTS['pgadmin_default_email']}"
        )
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
        f"Service '{image}' has incorrect tag. " f"Expected: '{expected_tag}'"
    )


def test_worker_services(rendered_folder):
    """Test that the number of worker containers matches the respective variables."""
    worker_names = {
        "num_tensorflow_cpu_workers": "tfcpu",
        "num_tensorflow_gpu_workers": "tfgpu",
        "num_pytorch_cpu_workers": "pytorchcpu",
        "num_pytorch_gpu_workers": "pytorchgpu",
    }

    deployment_name = EXPECTED_DEFAULTS["deployment_name"]
    docker_compose_path = os.path.join(rendered_folder, "docker-compose.yml")

    assert (
        docker_compose_path
    ), f"Docker compose file not found at '{docker_compose_path}'"

    with open(docker_compose_path, "r") as file:
        docker_compose = yaml.safe_load(file)

    services = docker_compose.get("services", {})

    for worker_type, service_suffix in worker_names.items():
        expected_count = int(EXPECTED_DEFAULTS[worker_type])

        for i in range(1, expected_count + 1):
            # ':02d' to ensure that the number is expressed as 2 digits
            service_name = f"{deployment_name}-{service_suffix}-{i:02d}"
            assert (
                service_name in services
            ), f"Missing service: {service_name} for {worker_type}"

        # Check if there is a worker index above what is expected
        extra_service_name = (
            f"{deployment_name}-{service_suffix}-{expected_count +1:02d}"
        )
        assert extra_service_name not in services, (
            f"Unexpected service: {extra_service_name} for {worker_type}; "
            f"expected count of {expected_count}"
        )
