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
from pathlib import Path

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient
from dioptra.client.utils import select_files_in_directory, select_one_or_more_files

# -- Tests -----------------------------------------------------------------------------


def test_upload_files(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    tmp_path: Path,
) -> None:
    (tmp_path / "subdir").mkdir()
    fake_file1_path = tmp_path / "fake_file1.txt"
    fake_file2_path = tmp_path / "fake_file2.txt"
    fake_file3_path = tmp_path / "subdir" / "fake_file3.txt"

    with (
        fake_file1_path.open("wt") as f1,
        fake_file2_path.open("wt") as f2,
        fake_file3_path.open("wt") as f3,
    ):
        f1.write("This is a test file.")
        f2.write("This is also a test file.")
        f3.write("This is yet another test file.")

    fake_file1_size = os.stat(fake_file1_path).st_size
    fake_file2_size = os.stat(fake_file2_path).st_size
    fake_file3_size = os.stat(fake_file3_path).st_size

    response = dioptra_client.echoes.create(
        test_files=select_files_in_directory(tmp_path, recursive=True),
        test_string="A test",
    )
    response_dict = response.json()

    assert response_dict["testString"] == "A test"
    assert response_dict["testFilesInfo"][0]["filename"] == "fake_file1.txt"
    assert response_dict["testFilesInfo"][1]["filename"] == "fake_file2.txt"
    assert response_dict["testFilesInfo"][2]["filename"] == "subdir/fake_file3.txt"
    assert response_dict["testFilesInfo"][0]["size"] == fake_file1_size
    assert response_dict["testFilesInfo"][1]["size"] == fake_file2_size
    assert response_dict["testFilesInfo"][2]["size"] == fake_file3_size


def test_upload_single_file(
    dioptra_client: DioptraClient[DioptraResponseProtocol],
    tmp_path: Path,
) -> None:
    fake_file_path = tmp_path / "fake_file1.txt"

    with fake_file_path.open("wt") as f:
        f.write("This is a test file.")

    fake_file_size = os.stat(fake_file_path).st_size

    response = dioptra_client.echoes.create_single(
        test_file=select_one_or_more_files([fake_file_path])[0],
        test_string="A single file test",
    )
    response_dict = response.json()

    assert response_dict["testString"] == "A single file test"
    assert response_dict["testFileInfo"]["filename"] == str(fake_file_path.name)
    assert response_dict["testFileInfo"]["size"] == fake_file_size
