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
from __future__ import annotations

import tarfile
import textwrap
from pathlib import Path
from typing import cast

import pytest
import testinfra
from docker.models.containers import Container
from testinfra.host import Host

from tests.utils import Timer

from ..utils import DioptraImages, DockerClient, start_container


@pytest.fixture(scope="module")
def container(docker_client: DockerClient, dioptra_images: DioptraImages) -> Container:
    c = start_container(
        client=docker_client,
        image=dioptra_images["mlflow_tracking"],
        entrypoint=[
            "/usr/local/bin/entrypoint.sh",
            "--default-artifact-root",
            "file:///work/artifacts",
        ],
    )
    yield c
    c.stop()


@pytest.fixture(scope="module")
def host(container: Container) -> Host:
    container_id: str = container.id
    return testinfra.get_host(f"docker://{container_id}")


@pytest.fixture(scope="function")
def print_db_tables_pyscript(container: Container, tmp_path: Path) -> str:
    pyscript: str | bytes = """
    import sqlite3\n

    con = sqlite3.connect("/work/mlruns/mlflow-tracking.db")
    cur = con.cursor()\n

    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")\n

    for row in cur:
        for table_name, in cur:
            print(table_name)\n

    con.close()
    """
    pyscript = textwrap.dedent(cast(str, pyscript)).encode("utf-8")
    pyscript_path = tmp_path / "print_db_tables.py"
    tarfile_path = tmp_path / "print_db_tables.tar"

    with pyscript_path.open("wb") as f:
        f.write(pyscript)

    with tarfile_path.open("wb") as saved_tar, pyscript_path.open("rb") as f:
        with tarfile.open(fileobj=saved_tar, mode="w") as tar:
            info = tar.gettarinfo(arcname="print_db_tables.py", fileobj=f)
            tar.addfile(info, f)

    with tarfile_path.open("rb") as saved_tar:
        container.put_archive(path="/work", data=saved_tar)

    return str(Path("/") / "work" / "print_db_tables.py")


def test_db_exists(host: Host, print_db_tables_pyscript: str) -> None:
    with Timer(timeout=60) as timer:
        while not host.file("/work/mlruns/mlflow-tracking.db").exists:
            if timer.timeout_exceeded:
                raise TimeoutError("Failed to create mlflow-tracking.db.")

        while not host.file("/work/mlruns/mlflow-tracking.db").size > 0:
            if timer.timeout_exceeded:
                raise TimeoutError("Failed to initialize mlflow-tracking.db.")

    cmd = "python %s"
    result = host.run(cmd, print_db_tables_pyscript)

    tables = result.stdout.split("\n")

    assert result.rc == 0
    assert len(tables) > 0
    assert "metrics" in tables
    assert "registered_models" in tables
    assert "runs" in tables
