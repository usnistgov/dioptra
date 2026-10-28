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
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml


def test_api_key_volume_and_initializer(result, context):
    """Give the initializer write access and both API services read access.

    Rendered services must select the same image, key path and named volume.
    Only the one-shot command writes application data; it inherits the image's
    normal user and needs neither certificate storage nor backing services.
    """
    assert result.exit_code == 0
    project = result.project_path
    initialization = yaml.safe_load((project / "docker-compose.init.yml").read_text())
    deployment = yaml.safe_load((project / "docker-compose.yml").read_text())
    initializer = initialization["services"]["init-restapi-key"]
    bootstrap = initialization["services"]["restapi"]
    api = deployment["services"][f"{context['__project_slug']}-restapi"]

    assert initializer["image"] == bootstrap["image"] == api["image"]
    assert initializer["entrypoint"] == ["dioptra-api"]
    assert initializer["command"] == ["init-key"]
    assert "user" not in initializer
    assert not initializer.get("depends_on")
    assert initializer["network_mode"] == "none"
    assert initializer["volumes"] == ["restapi-data:/work/data/restapi:rw"]
    for service in (bootstrap, api):
        assert "restapi-data:/work/data/restapi:ro" in service["volumes"]
        assert initializer["env_file"][0] in service["env_file"]
    environment = (project / initializer["env_file"][0]).read_text().splitlines()
    assert (
        "DIOPTRA_RESTAPI_SECRET_KEY_FILE=/work/data/restapi/secret-key" in environment
    )
    for configuration in (initialization, deployment):
        assert configuration["volumes"]["restapi-data"]["name"] == (
            f"{context['__project_slug']}_restapi-data"
        )
    assert (
        "restapi-data:/volumes/restapi-data:rw"
        in initialization["services"]["named-volumes"]["volumes"]
    )
    assert "minio" in initialization["services"]
    assert f"{context['__project_slug']}-minio" in deployment["services"]


@pytest.mark.parametrize("initializer_status", [0, 17])
def test_api_key_initialization_order(result, initializer_status):
    """Stop deployment setup when key initialization fails before API startup.

    Unrelated deployment operations are deliberately replaced with event
    recording, and the Compose call receives an injected exit status. The real
    main sequence must prepare volumes before invoking the one-shot command and
    must reach the bootstrap API only when that command succeeds.
    """
    source = (result.project_path / "init-deployment.sh").read_text()
    definitions, separator, _ = source.rpartition('main "${@}"')
    assert separator
    events = ["init_named_volumes", "start_restapi_service"]
    unrelated = [
        "parse_args",
        "init_templates",
        "init_scripts",
        "init_extra_ca_certificates",
        "start_minio_service",
        "init_minio",
        "stop_services",
        "init_frontend",
        "start_db_service",
        "manage_postgres_ssl",
        "init_worker_account",
    ]
    replacements = [f"{name}() {{ :; }}" for name in unrelated]
    replacements.extend(f"{name}() {{ echo {name}; }}" for name in events)
    replacements.append(
        f'docker_compose() {{ printf "%s\\n" "$*"; return {initializer_status}; }}'
    )
    completed = subprocess.run(
        [
            "bash",
            "-c",
            definitions + "\n" + "\n".join(replacements) + "\nmain",
            "./init-deployment.sh",
        ],
        cwd=result.project_path,
        capture_output=True,
        text=True,
    )
    lines = completed.stdout.splitlines()
    assert lines, completed.stderr
    assert lines[0] == "init_named_volumes"
    assert lines[1].endswith("run --rm init-restapi-key")
    if initializer_status:
        assert completed.returncode == initializer_status
        assert "start_restapi_service" not in lines
    else:
        assert completed.returncode == 0, completed.stderr
        assert lines[2] == "start_restapi_service"


@pytest.mark.skipif(shutil.which("argbash") is None, reason="Argbash is not installed")
def test_restapi_entrypoint_preserves_native_arguments(tmp_path, monkeypatch):
    """Preserve native Gunicorn arguments through the compiled shell parser.

    Compile the actual entrypoint and replace only database/server commands with
    local executables so no installed Dioptra or backing services are required.
    Options after --, including certificate paths containing spaces, must reach
    the production launcher unchanged instead of being dropped or split.
    """
    source = Path(__file__).resolve().parents[2]
    entrypoint = tmp_path / "entrypoint.sh"
    subprocess.run(
        [
            "argbash",
            str(source / "docker/shellscripts/entrypoint-restapi.m4"),
            "-o",
            str(entrypoint),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    commands = tmp_path / "bin"
    commands.mkdir()
    database = commands / "dioptra-db"
    database.write_text("#!/bin/sh\nexit 0\n")
    launcher = commands / "dioptra-api"
    launcher.write_text('#!/bin/sh\nprintf \'%s\\0\' "$@" > "$ARGUMENTS_FILE"\n')
    database.chmod(0o755)
    launcher.chmod(0o755)
    arguments = tmp_path / "arguments"
    monkeypatch.setenv("ARGUMENTS_FILE", str(arguments))
    monkeypatch.setenv("DIOPTRA_WORKDIR", str(tmp_path))
    monkeypatch.setenv("PATH", str(commands) + os.pathsep + os.environ["PATH"])
    native = ["--workers", "2", "--certfile", "/tmp/server certificate.crt"]
    subprocess.run(
        ["bash", str(entrypoint), "--", *native],
        check=True,
        capture_output=True,
        text=True,
    )
    assert arguments.read_bytes().split(b"\0")[:-1] == [
        value.encode()
        for value in ["prod", "-c", "/etc/gunicorn/gunicorn.conf.py", *native]
    ]
