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


@pytest.mark.skipif(
    os.name != "posix", reason="deployment scripts require a POSIX shell"
)
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
