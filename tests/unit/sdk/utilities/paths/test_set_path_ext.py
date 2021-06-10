# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
from pathlib import Path

import pytest

from mitre.securingai.sdk.utilities.paths import set_path_ext


@pytest.mark.parametrize("ext", ["csv", "csv.gz", "json"])
@pytest.mark.parametrize(
    "filepath",
    [
        "data.csv",
        "data.csv.gz",
        "data.dat.csv.gz",
        "/tmp/dir/data.csv",
        "/tmp/dir/data.csv.gz",
        "../dir/data.csv.gz",
    ],
)
def test_set_path_ext(filepath, ext) -> None:
    expected: str = f"data.{ext}"
    result: Path = set_path_ext(filepath=filepath, ext=ext)

    assert expected == result.name and Path(filepath).parent / expected == result
