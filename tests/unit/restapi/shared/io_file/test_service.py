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
from pathlib import Path
from typing import BinaryIO, List

import pytest
import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai.restapi.shared.io_file.service import IOFileService

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
    clean_file_path1: Path = io_file_service.sanitize_file_path(
        filepath="dir/subdir/testfile.txt", path_prefix="/tmp"
    )
    clean_file_path2: Path = io_file_service.sanitize_file_path(
        filepath="dir/subdir/testfile.txt"
    )
    clean_file_path3: Path = io_file_service.sanitize_file_path(
        filepath="../testfile.txt", path_prefix="/tmp"
    )

    assert clean_file_path1 == Path("/tmp") / "testfile.txt"
    assert clean_file_path2 == Path.cwd() / "testfile.txt"
    assert clean_file_path3 == Path("/tmp") / "testfile.txt"
