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

from dioptra import pyplugs
import tarfile
from pathlib import Path
from typing import Any, Callable, Dict, Literal, Optional

import pandas as pd
import structlog
from structlog.stdlib import BoundLogger

import abc as abc

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class FileArtifactError(Exception):
    """An error with the file artifact was detected."""


class UnsupportedDataFrameFileFormatError(Exception):
    """The requested data frame file format is not supported."""


class UnsupportedTarFileFormatError(Exception):
    """The tar file format was unexpected."""


class ArtifactHandlerInterface(abc.ABCMeta):
    @staticmethod
    @abc.abstractmethod
    def serialize(working_dir: Path, name: str, contents: Any, **kwargs) -> Path:
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def deserialize(working_dir: Path, path: str, **kwargs) -> Any:
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def validation() -> str | None:
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def name() -> str:
        raise NotImplementedError


@pyplugs.register
class FileArtifactHandler(ArtifactHandlerInterface):
    @staticmethod
    def serialize(working_dir: Path, name: str, contents: str, **kwargs) -> Path:
        result = working_dir / contents
        if not result.exists() or not result.is_file():
            LOGGER.error("{contents} is missing or not a file")
            raise FileArtifactError("{contents} is missing or not a file")
        return result

    @staticmethod
    def deserialize(working_dir: Path, path: str, **kwargs) -> Path:
        return working_dir / path

    @staticmethod
    def validation() -> str | None:
        return None

    @staticmethod
    def name() -> str:
        return "file"


@pyplugs.register
class DirectoryArtifactHandler(ArtifactHandlerInterface):
    @staticmethod
    def serialize(
        working_dir: Path,
        name: str,
        contents: str,
        tarball_write_mode: Literal["w", "w:", "w:gz", "x:bz2", "w:xz"] = "w:gz",
        **kwargs,
    ) -> Path:
        source_dir = working_dir / Path(contents)

        tarball_path = working_dir / name
        tarball_path = tarball_path.with_suffix(".tar")

        with tarfile.open(tarball_path, tarball_write_mode) as f:
            f.add(source_dir, arcname=source_dir.name)

        LOGGER.info(
            "Directory added to tar archive",
            directory=source_dir,
            tarball_path=tarball_path,
        )
        return tarball_path

    @staticmethod
    def deserialize(working_dir: Path, path: str, **kwargs) -> Path:
        name: str
        try:
            with tarfile.open(path, mode="r:*") as tar:
                tar.extractall(path=working_dir, filter="data")
                names = tar.getnames()
                if len(names) < 1:
                    raise UnsupportedTarFileFormatError(
                        "Tar file must have at least one entry."
                    )
                name = names[0]
        except Exception as e:
            LOGGER.exception("Could not extract from tar file")
            raise e

        return working_dir / name

    @staticmethod
    def validation() -> str | None:
        return None

    @staticmethod
    def name() -> str:
        return "directory"


@pyplugs.register
class DataframeArtifactHandler(ArtifactHandlerInterface):
    @staticmethod
    def serialize(
        working_dir: Path,
        name: str,
        contents: pd.DataFrame,
        format: str = "json",
        **kwargs,
    ) -> Path:
        """Serializes a :py:class:`~pandas.DataFrame` as an artifact..

        The `format` argument selects the :py:class:`~pandas.DataFrame` serializer,
        which are all handled using the object's `DataFrame.to_{format}` methods. The
        string passed to `format` must match one of the following,

        - `csv[.bz2|.gz|.xz]` - A comma-separated values plain text file with optional
        compression.
        - `feather` - A binary feather file.
        - `json` - A plain text JSON file.
        - `pickle` - A binary pickle file.
        - `parquet` - A parquet file

        Args:
            name: The name of the artifact to use for the serialized
            :py:class:`~pandas.DataFrame`.
            content: A :py:class:`~pandas.DataFrame` to be stored.
            format: The :py:class:`~pandas.DataFrame` file serialization format.
            kwargs: A dictionary of additional keyword arguments to pass to the
                serializer.

        Notes:
            The :py:mod:`pyarrow` package must be installed in order to serialize to the
            feather format.

        See Also:
            - :py:meth:`pandas.DataFrame.to_csv`
            - :py:meth:`pandas.DataFrame.to_feather`
            - :py:meth:`pandas.DataFrame.to_json`
            - :py:meth:`pandas.DataFrame.to_pickle`
            - :py:meth:`pandas.DataFrame.to_parquet`
        """
        filepath: Path = working_dir / name
        format_funcs = {
            "csv": {"func": contents.to_csv, "ext": ".csv"},
            "csv.bz2": {"func": contents.to_csv, "ext": ".csv.bz2"},
            "csv.gz": {"func": contents.to_csv, "ext": ".csv.gz"},
            "csv.xz": {"func": contents.to_csv, "ext": ".csv.xz"},
            "feather": {"func": contents.to_feather, "ext": ".feather"},
            "json": {"func": contents.to_json, "ext": ".json"},
            "pickle": {"func": contents.to_pickle, "ext": ".pkl"},
            "parquet": {"func": contents.to_parquet, "ext": ".parquet"},
        }

        formatter: Optional[Dict[str, Any]] = format_funcs.get(format)

        if formatter is None:
            message: str = (
                f"Serializing data frames to the {format} format is not supported"
            )
            LOGGER.error(message)
            raise UnsupportedDataFrameFileFormatError(message)

        df_to_format_func: Callable[..., None] = formatter["func"]
        df_artifact_path: Path = filepath.with_suffix(formatter["ext"])

        df_to_format_func(df_artifact_path, **kwargs)
        LOGGER.info(
            "Data frame saved to file",
            file_name=df_artifact_path.name,
            file_format=format,
        )
        return df_artifact_path

    @staticmethod
    def deserialize(working_dir: Path, path: str, **kwargs) -> pd.DataFrame:
        input = working_dir / path
        format_funcs = {
            ".csv": {"func": pd.read_csv, "args": {"index_col": 0}},
            ".bz2": {"func": pd.read_csv, "args": {"index_col": 0}},
            ".gz": {"func": pd.read_csv, "args": {"index_col": 0}},
            ".xz": {"func": pd.read_csv, "args": {"index_col": 0}},
            ".feather": {"func": pd.read_feather, "args": {}},
            ".json": {"func": pd.read_json, "args": {}},
            ".pkl": {"func": pd.read_pickle, "args": {}},
            ".parquet": {"func": pd.read_parquet, "args": {}},
        }

        formatter: Optional[Dict[str, Any]] = format_funcs.get(input.suffix)
        if formatter is None:
            message: str = (
                f"Deserializing file in {input.suffix} to data frames is not supported"
            )
            LOGGER.error(message)
            raise UnsupportedDataFrameFileFormatError(message)

        format_to_df: Callable[..., pd.DataFrame] = formatter["func"]
        return format_to_df(input, **formatter["args"])

    @staticmethod
    def validation() -> str | None:
        return None

    @staticmethod
    def name() -> str:
        return "dataframe"
