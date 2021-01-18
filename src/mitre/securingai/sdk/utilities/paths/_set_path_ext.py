from pathlib import Path
from typing import Union


def set_path_ext(filepath: Union[str, Path], ext: str) -> Path:
    ext = f".{ext.lstrip('.')}"
    filename: Union[str, Path] = Path(filepath)
    filepath = Path(filepath)

    for _ in filepath.suffixes:
        filename = Path(filename).stem

    return filepath.with_name(f"{Path(filename).with_suffix(ext)}")
