from __future__ import annotations

import os
import pickle
from pathlib import Path
from typing import Any

import structlog
from structlog.stdlib import BoundLogger

from dioptra.sdk.api.artifact import ArtifactTaskInterface

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class MatplotlibArtifactTask(ArtifactTaskInterface):
    """Save PNG in CWD and pickle the Figure in working_dir; return the pickle path."""

    @staticmethod
    def serialize(working_dir: Path, name: str, contents: Any, **kwargs) -> Path:
        os.environ.setdefault("MPLBACKEND", "Agg")
        png_path = (Path.cwd() / name).with_suffix(".png")
        try:
            contents.savefig(png_path, dpi=150, bbox_inches="tight")  # type: ignore[attr-defined]
            LOGGER.info("Saved PNG in CWD", png_path=str(png_path))
        except Exception:
            LOGGER.exception("Failed to save PNG (continuing)")

        pkl_path = (working_dir / name).with_suffix(".pkl")
        with open(pkl_path, "wb") as f:
            pickle.dump(contents, f)
        LOGGER.info("Pickled Matplotlib figure", pickle_path=str(pkl_path))
        return pkl_path

    @staticmethod
    def deserialize(working_dir: Path, path: str, **kwargs) -> Any:
        os.environ.setdefault("MPLBACKEND", "Agg")
        # Import here so pickle can resolve the Figure class.
        import matplotlib  # noqa: F401
        with open(working_dir / path, "rb") as f:
            fig = pickle.load(f)
        return fig

    @staticmethod
    def validation() -> dict[str, Any] | None:
        return None
