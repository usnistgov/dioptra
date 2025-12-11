from __future__ import annotations

from pathlib import Path
from typing import Any
import structlog
from structlog.stdlib import BoundLogger
# [new-imports]
import os
import pickle
import io
# [end-new-imports]

from dioptra.sdk.api.artifact import ArtifactTaskInterface

LOGGER: BoundLogger = structlog.stdlib.get_logger()


# [Plugin-definition]
class MatplotlibArtifactTask(ArtifactTaskInterface):
    """Save PNG in working_dir and return the PNG path. Deserialize returns PNG bytes."""

    @staticmethod
    def serialize(working_dir: Path, name: str, contents: Any, **kwargs) -> Path:
        os.environ.setdefault("MPLBACKEND", "Agg")
        png_path = (working_dir / name).with_suffix(".png")
        contents.savefig(png_path, dpi=150, bbox_inches="tight")  # type: ignore[attr-defined]
        return png_path

    @staticmethod
    def deserialize(working_dir: Path, path: str, **kwargs) -> bytes:
        png_file_path = working_dir / path
        with open(png_file_path, "rb") as f:
            png_data = f.read()
        return png_data

    @staticmethod
    def validation() -> dict[str, Any] | None:
        return None