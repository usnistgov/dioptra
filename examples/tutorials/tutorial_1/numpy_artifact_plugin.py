from pathlib import Path
from typing import Any

import numpy as np
import structlog

LOGGER = structlog.get_logger()
from dioptra.sdk.api.artifact import ArtifactTaskInterface


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
