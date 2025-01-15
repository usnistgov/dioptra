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
import re
from pathlib import Path

import pytest

from dioptra.client import (
    DioptraFile,
    select_files_in_directory,
    select_one_or_more_files,
)


@pytest.fixture
def fake_directory(tmp_path: Path) -> Path:
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "subdir2").mkdir()
    (tmp_path / "subdir" / "file1.txt").write_text("Content of file1")
    (tmp_path / "subdir" / "file2.txt").write_text("Content of file2")
    (tmp_path / "subdir" / "subdir2" / "file1.txt").write_text("Content of file1")
    (tmp_path / "subdir" / "subdir2" / "file3.md").write_text("# Content of file3")
    (tmp_path / "file4.txt").write_text("Content of file4")
    return tmp_path


@pytest.mark.parametrize(
    "recursive, include_pattern, expected_filenames",
    [
        (False, None, {"file4.txt"}),
        (
            True,
            None,
            {
                "file4.txt",
                "subdir/file1.txt",
                "subdir/file2.txt",
                "subdir/subdir2/file1.txt",
                "subdir/subdir2/file3.md",
            },
        ),
        (True, r".*\.md", {"subdir/subdir2/file3.md"}),
        (True, re.compile(r".*\.md"), {"subdir/subdir2/file3.md"}),
        (
            True,
            r".*\.txt",
            {
                "file4.txt",
                "subdir/file1.txt",
                "subdir/file2.txt",
                "subdir/subdir2/file1.txt",
            },
        ),
    ],
)
def test_select_files_in_directory(
    fake_directory: Path,
    recursive: bool,
    include_pattern: str | re.Pattern | None,
    expected_filenames: set[str],
) -> None:
    # Select the files from the temporary directory
    selected_files = select_files_in_directory(
        fake_directory, recursive=recursive, include_pattern=include_pattern
    )

    # Extract filenames to validate their paths
    filenames = [dioptra_file.filename for dioptra_file in selected_files]

    # Validate that all filenames match the expected relative POSIX paths
    assert set(filenames) == expected_filenames

    # Verify DioptraFile structure
    for dioptra_file in selected_files:
        assert isinstance(dioptra_file, DioptraFile)
        assert dioptra_file.stream.readable()


@pytest.mark.parametrize(
    "relative_file_paths, renames, expected_filenames",
    [
        (["file4.txt"], None, {"file4.txt"}),
        (
            [
                "file4.txt",
                "subdir/file1.txt",
                "subdir/file2.txt",
                "subdir/subdir2/file3.md",
            ],
            None,
            {"file4.txt", "file1.txt", "file2.txt", "file3.md"},
        ),
        (["subdir/subdir2/file3.md"], None, {"file3.md"}),
        (["subdir/subdir2/file3.md", "file4.txt"], None, {"file3.md", "file4.txt"}),
        (
            ["file4.txt", "subdir/file1.txt", "subdir/subdir2/file1.txt"],
            {"subdir/subdir2/file1.txt": "file1_copy.txt"},
            {"file1.txt", "file4.txt", "file1_copy.txt"},
        ),
    ],
)
def test_select_one_or_more_files(
    fake_directory: Path,
    relative_file_paths: list[str],
    renames: dict[str | Path, str] | None,
    expected_filenames: set[str],
) -> None:
    file_paths: list[str | Path] = [
        fake_directory / file_path for file_path in relative_file_paths
    ]
    if renames is not None:
        renames = {
            str(fake_directory / relative_path): new_filename
            for relative_path, new_filename in renames.items()
        }

    # Select the files from the temporary directory
    selected_files = select_one_or_more_files(file_paths, renames=renames)

    # Extract filenames for validation
    filenames = [dioptra_file.filename for dioptra_file in selected_files]

    # Validate that list of selected filenames match the expected ones after renaming
    assert set(filenames) == set(expected_filenames)

    # Verify DioptraFile structure
    for dioptra_file in selected_files:
        assert isinstance(dioptra_file, DioptraFile)
        assert dioptra_file.stream.readable()


def test_select_one_or_more_with_duplicate_filename_fails(
    fake_directory: Path,
) -> None:
    relative_file_paths = ["file4.txt", "subdir/file1.txt", "subdir/subdir2/file1.txt"]
    file_paths: list[str | Path] = [
        fake_directory / file_path for file_path in relative_file_paths
    ]

    with pytest.raises(ValueError):
        select_one_or_more_files(file_paths)


@pytest.mark.parametrize(
    "filename",
    [
        "/home/username/script.py",
        "../script.py",
        ".../script.py",
        "..../script.py",
        "../a/./script.py",
        "../a/.../script.py",
        "./a/script.py",
        "a//script.py",
        "a/.../script.py",
        "a/b/",
        "a/b/../script.py",
        "a\\script.py",
        "a\\..\\script.py",
        "a\\b/script.py",
        "C:\\Users\\username\\script.py",
    ],
)
def test_invalid_dioptra_filenames_fail(filename: str) -> None:
    with pytest.raises(ValueError):
        DioptraFile(
            filename=filename,
            stream=None,  # type: ignore[arg-type]
            content_type=None,
        )
