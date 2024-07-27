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
import io
import os
from pathlib import Path
from typing import BinaryIO, List, Optional, Union

import pytest
import structlog
from structlog.stdlib import BoundLogger

from dioptra.restapi.v1.shared.io_file_service import (
    IOFileService,
    UnsafeArchiveMemberPath,
)
from tests.utils import make_tarball_bytes

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.fixture
def io_file_service(dependency_injector) -> IOFileService:
    return dependency_injector.get(IOFileService)


def test_safe_extract_archive(
    io_file_service: IOFileService,
    task_plugin_archive: BinaryIO,
    tmp_path: Path,
) -> None:
    output_dir: Path = tmp_path / "extracted_plugins"
    output_dir.mkdir()

    extracted_files: List[str] = io_file_service.safe_extract_archive(
        output_dir=output_dir,
        archive_fileobj=task_plugin_archive,
    )

    expected_extracted_files: List[str] = [
        str(output_dir / x) for x in ["__init__.py", "plugin_module.py"]
    ]

    assert set(extracted_files) == set(expected_extracted_files)


def test_sanitize_file_path(io_file_service: IOFileService) -> None:
    clean_file_path1 = io_file_service.sanitize_file_path(
        filepath="dir/subdir/testfile.txt", path_prefix="/tmp"
    )
    clean_file_path2 = io_file_service.sanitize_file_path(
        filepath="dir/subdir/testfile.txt"
    )
    clean_file_path3 = io_file_service.sanitize_file_path(
        filepath="../testfile.txt", path_prefix="/tmp"
    )

    assert clean_file_path1 == Path("/tmp") / "testfile.txt"
    assert clean_file_path2 == Path.cwd() / "testfile.txt"
    assert clean_file_path3 == Path("/tmp") / "testfile.txt"


@pytest.mark.parametrize(
    "path, expected_result",
    [
        # assume fixed "/pre" prefix
        ("/foo/bar", "/pre/foo/bar"),
        ("foo/bar", "/pre/foo/bar"),
        ("/foo/../bar", None),
        ("foo/../bar", None),
    ],
)
def test_sanitize_file_path_preserve(
    io_file_service: IOFileService,
    path: str,
    expected_result: Optional[Union[str, Path]],
) -> None:
    actual_result = io_file_service.sanitize_file_path(path, "/pre", True)

    # wrap expected_result in a Path object, to make the below comparison work
    if expected_result is not None:
        expected_result = Path(expected_result)

    assert actual_result == expected_result


@pytest.mark.skipif(os.name != "nt", reason="requires Windows")
@pytest.mark.parametrize(
    "path, expected_result",
    [
        # assume fixed "/pre" prefix
        (r"C:\foo\bar", "/pre/foo/bar"),
        (r"C:foo\bar", "/pre/foo/bar"),
        (r"C:\foo\..\bar", None),
        (r"C:foo\..\bar", None),
    ],
)
def test_sanitize_file_path_preserve_windows(
    io_file_service: IOFileService,
    path: str,
    expected_result: Optional[Union[str, Path]],
) -> None:
    actual_result = io_file_service.sanitize_file_path(path, "/pre", True)

    # wrap expected_result in a Path object, to make the below comparison work
    if expected_result is not None:
        expected_result = Path(expected_result)

    assert actual_result == expected_result


def test_unsafe_tarball_path(tmp_path: Path, io_file_service: IOFileService) -> None:
    unsafe_tar_content = {
        "/a/b/c": b"123",
        "/a/../../b/c": b"456"
    }

    tarball_bytes = make_tarball_bytes(unsafe_tar_content)

    with pytest.raises(UnsafeArchiveMemberPath):
        io_file_service.safe_extract_archive(
            output_dir=tmp_path,
            archive_fileobj=io.BytesIO(tarball_bytes),
            preserve_paths=True,
        )
