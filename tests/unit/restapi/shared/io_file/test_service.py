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
