# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
from pathlib import Path
from typing import Union


def set_path_ext(filepath: Union[str, Path], ext: str) -> Path:
    ext = f".{ext.lstrip('.')}"
    filename: Union[str, Path] = Path(filepath)
    filepath = Path(filepath)

    for _ in filepath.suffixes:
        filename = Path(filename).stem

    return filepath.with_name(f"{Path(filename).with_suffix(ext)}")
