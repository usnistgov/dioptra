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
from pathlib import Path
from dataclasses import dataclass, field
import pandas as pd
from shutil import rmtree
import os

from dioptra.handlers.artifact import (
    FileArtifactHandler,
    DirectoryArtifactHandler,
    DataframeArtifactHandler,
    FileArtifactError,
)

# Set to False if generated temp files need to be inspected
cleanup: bool = True


@dataclass
class FileTest:
    name: str
    contents: str = "input"


@dataclass
class DirTest:
    name: str
    files: list[FileTest] = field(default_factory=list)
    dirs: list[DirTest] = field(default_factory=list)


def create_artifact(parent: Path, dir: DirTest):
    def create_directory_contents(
        path: Path, files: list[FileTest], dirs: list[DirTest]
    ):
        path.mkdir(exist_ok=True)
        for f in files:
            file = path / f.name
            if not file.exists():
                with open(file, "w+") as fp:
                    fp.write(f.contents)
        for d in dirs:
            create_directory_contents(path / d.name, d.files, d.dirs)

    parent.mkdir(parents=True, exist_ok=True)
    create_directory_contents(parent / dir.name, dir.files, dir.dirs)


@pytest.mark.parametrize("name, contents", [("artifact1", "file1")])
def test_file_handler(name: str, contents: str):
    work_dir = Path.cwd() / "tmp"
    create_artifact(Path.cwd(), DirTest("tmp", [FileTest(contents)]))
    result = FileArtifactHandler.serialize(work_dir, name, contents)
    assert result == (work_dir / contents)
    assert result.is_file()

    if cleanup:
        rmtree(work_dir)


@pytest.mark.parametrize("name, contents", [("artifact2", "file10")])
def test_file_handler_fail(name: str, contents: str):
    """Test to verify exception is thrown if file does not exist"""
    work_dir = Path.cwd() / "tmp"
    with pytest.raises(FileArtifactError):
        FileArtifactHandler.serialize(work_dir, name, contents)


@pytest.mark.parametrize(
    "name, ext, dir",
    [
        (
            "artifact1",
            "tar",
            DirTest(
                "dir1",
                [FileTest("file1"), FileTest("file2")],
                [
                    DirTest("sub1", [FileTest("file1-1"), FileTest("file1-2")]),
                    DirTest(
                        "sub2",
                        [FileTest("file2-1"), FileTest("file2-2")],
                        [
                            DirTest(
                                "sub2-1", [FileTest("file2-1-1"), FileTest("file2-1-2")]
                            )
                        ],
                    ),
                ],
            ),
        )
    ],
)
def test_directory_handler(name: str, ext: str, dir: DirTest):
    work_dir = Path.cwd() / "tmp"
    create_artifact(work_dir, dir)
    result = DirectoryArtifactHandler.serialize(work_dir, name, dir.name)

    assert result == (work_dir / f"{name}.{ext}")
    extracted = DirectoryArtifactHandler.deserialize(
        work_dir / "extracted", result.as_posix()
    )

    assert extracted.is_dir()

    # Validate that all entries are valid and have been created
    # this section may be overkill
    # build a dictionary of roots
    list = [(dir, work_dir / "extracted")]
    expected = {}
    for d, parent in list:
        path = (parent / d.name)
        expected[path.as_posix()] = d
        list.extend([(d, path) for d in d.dirs])

    count = 0
    for root, dirs, files in os.walk(extracted):
        count += 1
        # if this errors, missing directory entry
        current = expected[root]
        assert len(dirs) == len(current.dirs)
        # make sure there is one and only file entry for each entry
        for file in files:
            assert len([f for f in current.files if f.name == file]) == 1
    # make sure there are no extras
    assert count == len(expected)

    if cleanup:
        rmtree(work_dir)


@pytest.mark.parametrize(
    "name, data", [("artifact1", {"col1": [1, 2], "col2": ["a", "b"]})]
)
@pytest.mark.parametrize(
    "format, ext",
    [
        ("json", "json"),
        ("csv", "csv"),
        ("csv.bz2", "csv.bz2"),
        ("csv.gz", "csv.gz"),
        ("csv.xz", "csv.xz"),
        ("feather", "feather"),
        ("pickle", "pkl"),
        ("parquet", "parquet"),
    ],
)
def test_dataframe_handler(name: str, data: dict, format: str, ext: str):
    df = pd.DataFrame(data=data)

    work_dir = Path.cwd() / "tmp"
    work_dir.mkdir(exist_ok=True)
    result = DataframeArtifactHandler.serialize(work_dir, name, df, format=format)
    assert result == (work_dir / f"{name}.{ext}")
    assert result.is_file()

    des_df = DataframeArtifactHandler.deserialize(work_dir, f"{name}.{ext}")

    diff = df.compare(des_df)
    # must be no difference after a round-trip
    assert diff.empty

    if cleanup:
        rmtree(work_dir)
