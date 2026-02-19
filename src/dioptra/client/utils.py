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
import enum
import os
import re
from pathlib import Path

from .base import DioptraFile


class FileTypes(enum.Enum):
    """
    Available FileTypes
    """

    suffix: str

    def __new__(
        cls,
        value: str,
        suffix: str,
    ):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.suffix = suffix
        return obj

    TAR_GZ = "tar_gz", ".tar.gz"
    ZIP = "zip", ".zip"


def select_files_in_directory(
    dir_path: str | Path,
    recursive: bool = False,
    include_pattern: str | re.Pattern | None = None,
) -> list[DioptraFile]:
    """Select files in a directory.

    Args:
        dir_path: The path to the root directory to search for files.
        recursive: If True, search for files recursively in subdirectories.
            Defaults to False.
        include_pattern: A string or compiled regular expression pattern to use to
            filter files by name. If None, then all files are included. Defaults to
            None.

    Returns:
        A list of DioptraFile objects representing the selected files.

    Raises:
        FileNotFoundError: If the specified `dir_path` does not exist.
        NotADirectoryError: If `dir_path` is not a directory.
        IOError: If a file cannot be opened.
    """
    root_dir = Path(dir_path)

    # Ensure the root path exists and is a directory
    if not root_dir.is_dir():
        if not root_dir.exists():
            raise FileNotFoundError(
                f"Invalid directory path (reason: dir_path does not exist): {root_dir}"
            )

        raise NotADirectoryError(
            f"Invalid directory path (reason: dir_path is not a directory): {root_dir}"
        )

    # If provided, ensure that the include_pattern regular expression is compiled
    if include_pattern is not None and not isinstance(include_pattern, re.Pattern):
        include_pattern = re.compile(include_pattern)

    dioptra_files: list[DioptraFile] = []

    # Walk through the directory (optionally recursively)
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if not recursive:
            dirnames.clear()  # Prevent descending into subdirectories if not recursive

        current_dir = Path(dirpath)

        for filename in filenames:
            # Filter files based on the include_pattern, if provided
            if include_pattern is not None and not include_pattern.match(filename):
                continue  # Skip files that do not match the pattern

            current_file = current_dir / filename

            try:
                stream = open(current_file, "rb")

            except IOError as err:
                raise IOError(
                    f"File opening failed (reason: {err.strerror}): {current_file}"
                ) from err

            # Compute the relative path from the root directory
            relative_file_path = current_file.relative_to(root_dir)

            dioptra_files.append(
                DioptraFile(
                    filename=relative_file_path.as_posix(),  # Ensure POSIX-style paths
                    stream=stream,
                    content_type=None,
                )
            )

    return dioptra_files


def select_one_or_more_files(
    file_paths: list[str | Path], renames: dict[str | Path, str] | None = None
) -> list[DioptraFile]:
    """Select one or more files.

    Unlike `select_files_in_directory`, this is a flattening operation that only
    preserves each file's filename. The list of filenames must be unique.

    The `renames` dictionary is used to rename files, and can be used to ensure that the
    filenames are unique. Each key in the dictionary must exactly match one of the paths
    listed in `file_paths` (the paths are not resolved prior to matching).

    Args:
        file_paths: A list of file paths.
        renames: A dictionary mapping original file paths to new filenames. Only the
            file paths that are included will be renamed, the rest will be kept as-is.
            If None, then no renaming is performed. Defaults to None.

    Returns:
        A list of DioptraFile objects representing the selected files.

    Raises:
        ValueError: If a filename is not unique after applying `renames`.
        IOError: If a file cannot be opened.
    """
    dioptra_files: list[DioptraFile] = []
    filenames_seen: set[str] = set()  # Keep track of filenames to ensure uniqueness

    # Convert renames to a dictionary with Path objects as keys
    rename_mapping: dict[Path, str] = {}
    if renames is not None:
        for key, value in renames.items():
            rename_mapping[Path(key)] = value  # Ensure consistent key type

    for file_path in file_paths:
        current_file = Path(file_path)

        try:
            stream = open(current_file, "rb")

        except IOError as err:
            raise IOError(
                f"File opening failed (reason: {err.strerror}): {current_file}"
            ) from err

        # Determine the filename, applying renaming if specified
        current_filename = rename_mapping.get(current_file, current_file.name)

        # Ensure the filename is unique, raising an error if there's a conflict
        if current_filename in filenames_seen:
            if current_filename != current_file.name:
                raise ValueError(
                    "Invalid filename (reason: renamed filename is not unique): "
                    f"{current_file.name} -> {current_filename}"
                )

            raise ValueError(
                "Invalid filename (reason: filename is not unique, try renaming it): "
                f"{current_filename}"
            )

        filenames_seen.add(current_filename)  # Record the filename as seen
        dioptra_files.append(
            DioptraFile(
                filename=current_filename,
                stream=stream,
                content_type=None,
            )
        )

    return dioptra_files
