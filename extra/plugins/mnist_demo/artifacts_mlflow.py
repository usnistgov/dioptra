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
"""A task plugin module for MLFlow artifacts management.

This module contains a set of task plugins for managing artifacts generated during an
entry point run.
"""

import tarfile
from pathlib import Path
from typing import Any, Callable

import mlflow
import os
import pandas as pd
import structlog
from structlog.stdlib import BoundLogger

from dioptra import pyplugs
from dioptra.sdk.utilities.paths import set_path_ext

from .restapi import upload_artifact_to_restapi
from .artifacts_exceptions import UnsupportedDataFrameFileFormatError

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pyplugs.register
def download_all_artifacts(
    uris: list[str], 
    destinations: list[str]
) -> list[str]:
    download_paths: list[str] = []
    for uri in uris:
        for dest in destinations:
            if uri.endswith(dest):
                download_path: str = mlflow.artifacts.download_artifacts(
                    artifact_uri=uri
                )
                LOGGER.info(
                    "Artifact downloaded from MLFlow run",
                    artifact_path=download_path
                )
                download_paths.append(download_path)
    return download_paths


@pyplugs.register
def upload_data_frame_artifact(
    data_frame: pd.DataFrame,
    file_name: str,
    file_format: str,
    file_format_kwargs: dict[str, Any] | None = None,
    working_dir: str | Path | None = None,
) -> None:
    """Uploads a :py:class:`~pandas.DataFrame` as an artifact of the active MLFlow run.

    The `file_format` argument selects the :py:class:`~pandas.DataFrame` serializer,
    which are all handled using the object's `DataFrame.to_{format}` methods. The string
    passed to `file_format` must match one of the following,

    - `csv[.bz2|.gz|.xz]` - A comma-separated values plain text file with optional
      compression.
    - `feather` - A binary feather file.
    - `json` - A plain text JSON file.
    - `pickle` - A binary pickle file.

    Args:
        data_frame: A :py:class:`~pandas.DataFrame` to be uploaded.
        file_name: The filename to use for the serialized :py:class:`~pandas.DataFrame`.
        file_format: The :py:class:`~pandas.DataFrame` file serialization format.
        file_format_kwargs: A dictionary of additional keyword arguments to pass to the
            serializer. If `None`, then no additional keyword arguments are passed. The
            default is `None`.
        working_dir: The location where the file should be saved. If `None`, then the
            current working directory is used. The default is `None`.

    Notes:
        The :py:mod:`pyarrow` package must be installed in order to serialize to the
        feather format.

    See Also:
        - :py:meth:`pandas.DataFrame.to_csv`
        - :py:meth:`pandas.DataFrame.to_feather`
        - :py:meth:`pandas.DataFrame.to_json`
        - :py:meth:`pandas.DataFrame.to_pickle`
    """

    def to_format(
        data_frame: pd.DataFrame, format: str, output_dir: str|Path
    ) -> dict[str, Any]:
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

        func: dict[str, Any] | None = format_funcs.get(format)

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
    format_dict: dict[str, Any] = to_format(
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

def download_df(
    filename: str,
    format: str = 'csv',
    file_format_kwargs: dict[str, Any] | None = None,
) -> pd.DataFrame:
    file_format_kwargs = file_format_kwargs if file_format_kwargs is not None else {}
    def from_format(
        format: str
    ) -> dict[str, Any]:
        format_funcs = {
            "csv": {
                "func": pd.read_csv,
            },
            "csv.bz2": {
                "func": pd.read_csv,
            },
            "csv.gz": {
                "func": pd.read_csv,
            },
            "csv.xz": {
                "func": pd.read_csv,
            },
            "feather": {
                "func": pd.read_feather,
            },
            "json": {
                "func": pd.read_json,
            },
            "pickle": {
                "func": pd.read_pickle,
            },
        }

        func: dict[str, Any] | None = format_funcs.get(format)

        if func is None:
            raise UnsupportedDataFrameFileFormatError(
                f"Serializing data frames from the {format} format is not supported"
            )
        
        return func
    format_dict: dict[str, Any] = from_format(format=format)
    df_from_format_func: Callable[..., Any] = format_dict["func"]
    df: pd.DataFrame = df_from_format_func(filename, **file_format_kwargs)
    return df


@pyplugs.register
def upload_directory_as_tarball_artifact(
    source_dir: str | Path,
    tarball_filename: str,
    tarball_write_mode: str = "w:gz",
    working_dir: str | Path | None = None,
) -> None:
    """Archives a directory and uploads it as an artifact of the active MLFlow run.

    Args:
        source_dir: The directory which should be uploaded.
        tarball_filename: The filename to use for the archived directory tarball.
        tarball_write_mode: The write mode for the tarball, see :py:func:`tarfile.open`
            for the full list of compression options. The default is `"w:gz"` (gzip
            compression).
        working_dir: The location where the file should be saved. If `None`, then the
            current working directory is used. The default is `None`.

    See Also:
        - :py:func:`tarfile.open`
    """
    if working_dir is None:
        working_dir = Path.cwd()

    source_dir = Path(source_dir)
    working_dir = Path(working_dir)
    tarball_path = working_dir / tarball_filename

    with tarfile.open(tarball_path, tarball_write_mode) as f:  # type: ignore
        f.add(source_dir, arcname=source_dir.name)

    LOGGER.info(
        "Directory added to tar archive",
        directory=source_dir,
        tarball_path=tarball_path,
    )

    upload_file_as_artifact(artifact_path=tarball_path)


@pyplugs.register
def upload_file_as_artifact(artifact_path: str | Path) -> None:
    """Uploads a file as an artifact of the active MLFlow run.

    Args:
        artifact_path: The location of the file to be uploaded.

    See Also:
        - :py:func:`mlflow.log_artifact`
    """
    artifact_path = Path(artifact_path)
    mlflow.log_artifact(str(artifact_path))
    uri = mlflow.get_artifact_uri(str(artifact_path.name))
    upload_artifact_to_restapi(uri, os.environ['__JOB_ID'])
    LOGGER.info("Artifact uploaded for current MLFlow run", filename=artifact_path.name)
