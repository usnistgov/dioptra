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

from typing import Iterator, cast

import pytest
import testinfra
from docker.models.containers import Container
from testinfra.host import Host

from ..utils import (
    CONTAINER_FIXTURE_PARAMS,
    DioptraImages,
    DockerClient,
    start_container,
)

TEST_WORKDIR: str = "/test_workdir"


@pytest.fixture(
    scope="module",
    params=CONTAINER_FIXTURE_PARAMS,
)
def container(
    request, docker_client: DockerClient, dioptra_images: DioptraImages
) -> Iterator[Container]:
    c = start_container(
        client=docker_client,
        image=dioptra_images[request.param.replace("-", "_")],  # type: ignore[literal-required] # noqa: B950
        user="root:root",
        tmpfs={TEST_WORKDIR: ""},
        working_dir=TEST_WORKDIR,
    )
    yield c
    c.stop()


@pytest.fixture(scope="module")
def host(container: Container) -> Host:
    container_id: str = container.id
    return testinfra.get_host(f"docker://{container_id}")


@pytest.fixture(scope="function")
def temporary_file(host: Host) -> Iterator[str]:
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
def temporary_files_and_folders(host: Host) -> Iterator[dict[str, str | list[str]]]:
    tmproot_path = f"{TEST_WORKDIR}/tmproot"
    tmpfolder1_path = f"{tmproot_path}/tmpfolder1"
    tmpfolder2_path = f"{tmproot_path}/tmpfolder2"
    tmpfolder3_path = f"{tmpfolder2_path}/tmpfolder3"
    tmpfile_paths = [
        f"{tmproot_path}/tmpfile1.txt",
        f"{tmproot_path}/tmpfile2.txt",
        f"{tmpfolder1_path}/tmpfile3.txt",
        f"{tmpfolder1_path}/tmpfile4.txt",
        f"{tmpfolder2_path}/tmpfile5.txt",
        f"{tmpfolder2_path}/tmpfile6.txt",
        f"{tmpfolder3_path}/tmpfile7.txt",
        f"{tmpfolder3_path}/tmpfile8.txt",
    ]

    host.run("mkdir -p %s", tmpfolder1_path)
    host.run("mkdir -p %s", tmpfolder2_path)
    host.run("mkdir -p %s", tmpfolder3_path)
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
        "tmpfolder3": tmpfolder3_path,
        "tmpfiles": tmpfile_paths,
    }

    host.run(
        "find %s -name %s -o -prune -exec rm -rf -- %s %s",
        f"{TEST_WORKDIR}/.",
        ".",
        "{}",
        "+",
    )


class TestInitSetPermissions:
    @pytest.mark.parametrize(
        "new_owner,file_chmod", [("39000:100", "0640"), ("39000:100", "0600")]
    )
    def test_set_single_file_permissions(
        self, host: Host, temporary_file: str, new_owner: str, file_chmod: str
    ) -> None:
        new_uid, new_gid = [int(x) for x in new_owner.split(":")]

        cmd = host.run(
            "init-set-permissions.sh --file-chmod %s --chown %s %s",
            file_chmod,
            new_owner,
            temporary_file,
        )

        assert cmd.rc == 0
        assert host.file(temporary_file).uid == new_uid
        assert host.file(temporary_file).gid == new_gid
        assert host.file(temporary_file).mode == int(file_chmod, 8)

    @pytest.mark.parametrize(
        "new_owner,file_chmod,dir_chmod",
        [("39000:100", "0640", "0750"), ("39000:100", "0600", "0700")],
    )
    def test_set_recursive_permissions_on_root_dir(
        self,
        host: Host,
        temporary_files_and_folders: dict[str, str | list[str]],
        new_owner: str,
        file_chmod: str,
        dir_chmod: str,
    ) -> None:
        new_uid, new_gid = [int(x) for x in new_owner.split(":")]
        directories: list[str] = [
            cast(str, temporary_files_and_folders["tmproot"]),
            cast(str, temporary_files_and_folders["tmpfolder1"]),
            cast(str, temporary_files_and_folders["tmpfolder2"]),
            cast(str, temporary_files_and_folders["tmpfolder3"]),
        ]
        filepaths: list[str] = cast(list[str], temporary_files_and_folders["tmpfiles"])

        cmd = host.run(
            "init-set-permissions.sh --recursive --dir-chmod %s --file-chmod %s "
            "--chown %s %s",
            dir_chmod,
            file_chmod,
            new_owner,
            directories[0],
        )
        print(cmd.stdout)
        print(cmd.stderr)

        assert cmd.rc == 0

        for directory in directories:
            assert host.file(directory).uid == new_uid
            assert host.file(directory).gid == new_gid
            assert host.file(directory).mode == int(dir_chmod, 8)

        for filepath in filepaths:
            assert host.file(filepath).uid == new_uid
            assert host.file(filepath).gid == new_gid
            assert host.file(filepath).mode == int(file_chmod, 8)

    @pytest.mark.parametrize(
        "new_owner,file_chmod,dir_chmod",
        [("39000:100", "0640", "0750"), ("39000:100", "0600", "0700")],
    )
    def test_set_recursive_permissions_on_sub_dirs(
        self,
        host: Host,
        temporary_files_and_folders: dict[str, str | list[str]],
        new_owner: str,
        file_chmod: str,
        dir_chmod: str,
    ) -> None:
        new_uid, new_gid = [int(x) for x in new_owner.split(":")]
        root_directory: str = cast(str, temporary_files_and_folders["tmproot"])
        directories: list[str] = [
            cast(str, temporary_files_and_folders["tmpfolder1"]),
            cast(str, temporary_files_and_folders["tmpfolder2"]),
            cast(str, temporary_files_and_folders["tmpfolder3"]),
        ]
        root_filepaths: list[str] = cast(
            list[str], temporary_files_and_folders["tmpfiles"][:2]
        )
        subdir_filepaths: list[str] = cast(
            list[str], temporary_files_and_folders["tmpfiles"][2:]
        )

        cmd = host.run(
            "init-set-permissions.sh --recursive --dir-chmod %s --file-chmod %s "
            "--chown %s %s %s",
            dir_chmod,
            file_chmod,
            new_owner,
            directories[0],
            directories[1],
        )
        print(cmd.stdout)
        print(cmd.stderr)

        assert cmd.rc == 0
        assert host.file(root_directory).uid == 0
        assert host.file(root_directory).gid == 0
        assert host.file(root_directory).mode == int("0755", 8)

        for filepath in root_filepaths:
            assert host.file(filepath).uid == 0
            assert host.file(filepath).gid == 0
            assert host.file(filepath).mode == int("0644", 8)

        for directory in directories:
            assert host.file(directory).uid == new_uid
            assert host.file(directory).gid == new_gid
            assert host.file(directory).mode == int(dir_chmod, 8)

        for filepath in subdir_filepaths:
            assert host.file(filepath).uid == new_uid
            assert host.file(filepath).gid == new_gid
            assert host.file(filepath).mode == int(file_chmod, 8)
