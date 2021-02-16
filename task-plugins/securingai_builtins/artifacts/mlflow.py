import tarfile
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

import mlflow
import pandas as pd
import structlog
from mlflow.tracking import MlflowClient
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.utilities.paths import set_path_ext

from .exceptions import UnsupportedDataFrameFileFormatError

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
def download_all_artifacts_in_run(
    run_id: str, artifact_path: str, destination_path: Optional[str] = None
) -> str:
    """Download an artifact file or directory from a previous MLFlow run.

    Args:
        run_id: The unique identifier of a previous MLFlow run.
        artifact_path: The relative source path to the desired artifact.
        destination_path: The relative destination path where the artifacts will be
            downloaded. If ``None``, the artifacts will be downloaded to a new
            uniquely-named directory on the local filesystem. Defaults to ``None``.

    Returns:
        A string pointing to the directory containing the downloaded artifacts.
    """
    download_path: str = MlflowClient().download_artifacts(
        run_id=run_id, path=artifact_path, dst_path=destination_path
    )
    LOGGER.info(
        "Artifacts downloaded from MLFlow run",
        run_id=run_id,
        artifact_path=artifact_path,
        destination_path=download_path,
    )

    return download_path


@pyplugs.register
def upload_data_frame_artifact(
    data_frame: pd.DataFrame,
    file_name: str,
    file_format: str,
    file_format_kwargs: Optional[Dict[str, Any]] = None,
    working_dir: Optional[Union[str, Path]] = None,
) -> None:
    def to_format(
        data_frame: pd.DataFrame, format: str, output_dir: Union[str, Path]
    ) -> Dict[str, Any]:
        filepath: Path = Path(output_dir) / Path(file_name).name
        format_funcs = {
            "csv": {
                "func": data_frame.to_csv,
                "filepath": set_path_ext(filepath=filepath, ext="csv"),
            },
            "csv.bz2": {
                "func": data_frame.to_csv,
                "filepath": set_path_ext(filepath=filepath, ext="csv.bz2"),
            },
            "csv.gz": {
                "func": data_frame.to_csv,
                "filepath": set_path_ext(filepath=filepath, ext="csv.gz"),
            },
            "csv.xz": {
                "func": data_frame.to_csv,
                "filepath": set_path_ext(filepath=filepath, ext="csv.xz"),
            },
            "feather": {
                "func": data_frame.to_feather,
                "filepath": set_path_ext(filepath=filepath, ext="feather"),
            },
            "json": {
                "func": data_frame.to_json,
                "filepath": set_path_ext(filepath=filepath, ext="json"),
            },
            "pickle": {
                "func": data_frame.to_pickle,
                "filepath": set_path_ext(filepath=filepath, ext="pkl"),
            },
        }

        func: Optional[Dict[str, Any]] = format_funcs.get(format)

        if func is None:
            raise UnsupportedDataFrameFileFormatError(
                f"Serializing data frames to the {file_format} format is not supported"
            )

        return func

    if file_format_kwargs is None:
        file_format_kwargs = {}

    if working_dir is None:
        working_dir = Path.cwd()

    working_dir = Path(working_dir)
    format_dict: Dict[str, Any] = to_format(
        data_frame=data_frame, format=file_format, output_dir=working_dir
    )

    df_to_format_func: Callable[..., None] = format_dict["func"]
    df_artifact_path: Path = format_dict["filepath"]

    df_to_format_func(df_artifact_path, **file_format_kwargs)
    LOGGER.info(
        "Data frame saved to file",
        file_name=df_artifact_path.name,
        file_format=file_format,
    )

    upload_file_as_artifact(artifact_path=df_artifact_path)


@pyplugs.register
def upload_directory_as_tarball_artifact(
    source_dir: Union[str, Path],
    tarball_filename: str,
    tarball_write_mode: str = "w:gz",
    working_dir: Optional[Union[str, Path]] = None,
) -> None:
    if working_dir is None:
        working_dir = Path.cwd()

    source_dir = Path(source_dir)
    working_dir = Path(working_dir)
    tarball_path = working_dir / tarball_filename

    with tarfile.open(tarball_path, tarball_write_mode) as f:
        f.add(source_dir, arcname=source_dir.name)

    LOGGER.info(
        "Directory added to tar archive",
        directory=source_dir,
        tarball_path=tarball_path,
    )

    upload_file_as_artifact(artifact_path=tarball_path)


@pyplugs.register
def upload_file_as_artifact(artifact_path: Union[str, Path]) -> None:
    artifact_path = Path(artifact_path)
    mlflow.log_artifact(str(artifact_path))
    LOGGER.info("Artifact uploaded for current MLFlow run", filename=artifact_path.name)
