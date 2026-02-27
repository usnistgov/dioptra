# [numpy-plugin-definition]
from __future__ import annotations
from pathlib import Path
from typing import Any
import os

import numpy as np
import structlog

LOGGER = structlog.get_logger()
from dioptra.sdk.api.artifact import ArtifactTaskInterface


LOGGER: BoundLogger = structlog.stdlib.get_logger()

# Defining serialize and deserialize methods for ArtifactTaskMethod is required
class NumpyArrayArtifactTask(ArtifactTaskInterface):
    @staticmethod
    def serialize(working_dir: Path, name: str, contents: np.ndarray, **kwargs) -> Path:
        path = (working_dir / name).with_suffix(".npy")
        np.save(path, contents, allow_pickle=False)
        return path

    @staticmethod
    def deserialize(working_dir: Path, path: str, **kwargs) -> np.ndarray:
        return np.load(working_dir / path)

    @staticmethod
    def validation() -> dict[str, Any] | None:
        return None
# [end-numpy-plugin-definition]

# [pngbytes-plugin-definition]
# Paste this after the definition of 'NumpyArrayArtifactTask'
class PngBytesArtifactTask(ArtifactTaskInterface):
    """Save PNG bytes in working_dir and return the PNG path. Deserialize returns PNG bytes."""

    @staticmethod
    def serialize(working_dir: Path, name: str, contents: bytes, **kwargs) -> Path:
        """Writes raw PNG bytes to disk."""
        png_path = (working_dir / name).with_suffix(".png")
        
        # Write the incoming bytes directly to the file
        with open(png_path, "wb") as f:
            f.write(contents)
            
        return png_path

    @staticmethod
    def deserialize(working_dir: Path, path: str, **kwargs) -> bytes:
        """Reads raw PNG bytes from disk."""
        png_file_path = working_dir / path
        with open(png_file_path, "rb") as f:
            png_data = f.read()
        return png_data

    @staticmethod
    def validation() -> dict[str, Any] | None:
        return None
# [end-pngbytes-plugin-definition]