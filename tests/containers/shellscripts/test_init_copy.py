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

import pytest
import testinfra
from docker.models.containers import Container
from testinfra.host import Host

from ..utils import (
    CONTAINER_FIXTURE_PARAMS,
    TEST_WORKDIR,
    DioptraImages,
    DockerClient,
    start_container,
)


@pytest.fixture(
    scope="module",
    params=CONTAINER_FIXTURE_PARAMS,
)
def container(
    request, docker_client: DockerClient, dioptra_images: DioptraImages
) -> Container:
    c = start_container(
        client=docker_client,
        image=dioptra_images[request.param.replace("-", "_")],
        user="root:root",
    )
    yield c
    c.stop()


@pytest.fixture(scope="module")
def host(container: Container) -> Host:
    container_id: str = container.id
    return testinfra.get_host(f"docker://{container_id}")


@pytest.fixture(scope="function")
def temporary_file(host: Host) -> str:
    tmpfile_path = f"{TEST_WORKDIR}/tmpfile.txt"
    host.run("touch %s", tmpfile_path)
    host.run("chmod %s %s", "0644", tmpfile_path)
    host.run("chown %s %s", "root:root", tmpfile_path)
    yield tmpfile_path
    host.run(
        "find %s -name %s -o -prune -exec rm -rf -- %s %s",
        f"{TEST_WORKDIR}/.",
        ".",
        "{}",
        "+",
    )


@pytest.fixture(scope="function")
def temporary_files_and_folders(host: Host) -> dict[str, str]:
    tmproot_path = f"{TEST_WORKDIR}/tmproot"
    tmpfolder1_path = f"{tmproot_path}/tmpfolder1"
    tmpfolder2_path = f"{tmproot_path}/tmpfolder2"
    tmpfile_paths = [
        f"{tmproot_path}/tmpfile1.txt",
        f"{tmproot_path}/tmpfile2.txt",
        f"{tmpfolder1_path}/tmpfile3.txt",
        f"{tmpfolder1_path}/tmpfile4.txt",
        f"{tmpfolder2_path}/tmpfile5.txt",
        f"{tmpfolder2_path}/tmpfile6.txt",
    ]

    host.run("mkdir -p %s", tmpfolder1_path)
    host.run("mkdir -p %s", tmpfolder2_path)
    host.run("chmod -R %s %s", "0755", tmproot_path)
    host.run("chown -R %s %s", "root:root", tmproot_path)

    for filepath in tmpfile_paths:
        host.run("touch %s", filepath)
        host.run("chmod %s %s", "0644", filepath)
        host.run("chown %s %s", "root:root", filepath)

    yield {
        "tmproot": tmproot_path,
        "tmpfolder1": tmpfolder1_path,
        "tmpfolder2": tmpfolder2_path,
        "tmpfiles": tmpfile_paths,
    }

    host.run(
        "find %s -name %s -o -prune -exec rm -rf -- %s %s",
        f"{TEST_WORKDIR}/.",
        ".",
        "{}",
        "+",
    )


class TestInitCopy:
    @pytest.mark.parametrize(
        "chown,chmod", [("39000:100", "0640"), ("39000:100", "0600")]
    )
    def test_copy_files(
        self, host: Host, temporary_file: str, chown: str, chmod: str
    ) -> None:
        new_uid, new_gid = [int(x) for x in chown.split(":")]
        tmpfile_copy1_path = f"{TEST_WORKDIR}/tmpfile_copy1.txt"
        tmpfile_copy2_path = f"{TEST_WORKDIR}/tmpfile_copy2.txt"
        tmpfile_copies = [tmpfile_copy1_path, tmpfile_copy2_path]

        cmd = host.run(
            "init-copy.sh --chmod %s --chown %s %s %s %s %s",
            chmod,
            chown,
            temporary_file,
            tmpfile_copy1_path,
            temporary_file,
            tmpfile_copy2_path,
        )

        assert cmd.rc == 0

        assert host.file(temporary_file).uid == 0
        assert host.file(temporary_file).gid == 0
        assert host.file(temporary_file).mode == int("0644", 8)

        for filepath in tmpfile_copies:
            assert host.file(filepath).uid == new_uid
            assert host.file(filepath).gid == new_gid
            assert host.file(filepath).mode == int(chmod, 8)

    @pytest.mark.parametrize(
        "chown,chmod", [("39000:100", "0640"), ("39000:100", "0600")]
    )
    def test_set_recursive_permissions_on_root_dir(
        self,
        host: Host,
        temporary_files_and_folders: dict[str, str],
        chown: str,
        chmod: str,
    ) -> None:
        new_uid, new_gid = [int(x) for x in chown.split(":")]
        root_directory: str = temporary_files_and_folders["tmproot"]
        root_directory_copy: str = f"{TEST_WORKDIR}/tmproot_copy"
        subfolder_copies: list[str] = [
            root_directory_copy,
            f"{root_directory_copy}/tmpfolder1",
            f"{root_directory_copy}/tmpfolder2",
        ]
        filepath_copies: list[str] = [
            f"{subfolder_copies[0]}/tmpfile1.txt",
            f"{subfolder_copies[0]}/tmpfile2.txt",
            f"{subfolder_copies[1]}/tmpfile3.txt",
            f"{subfolder_copies[1]}/tmpfile4.txt",
            f"{subfolder_copies[2]}/tmpfile5.txt",
            f"{subfolder_copies[2]}/tmpfile6.txt",
        ]

        cmd = host.run(
            "init-copy.sh --recursive --chmod %s --chown %s %s %s",
            chmod,
            chown,
            root_directory,
            root_directory_copy,
        )

        assert cmd.rc == 0

        for directory in subfolder_copies:
            assert host.file(directory).uid == new_uid
            assert host.file(directory).gid == new_gid
            assert host.file(directory).mode == int("0755", 8)

        for filepath in filepath_copies:
            assert host.file(filepath).uid == new_uid
            assert host.file(filepath).gid == new_gid
            assert host.file(filepath).mode == int(chmod, 8)
