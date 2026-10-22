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
import re
from collections.abc import Iterator
from contextlib import ExitStack
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
    follow_symlinks: bool = False,
) -> list[DioptraFile]:
    """Select files in a directory.

    File and directory symlinks are skipped by default. When enabled, symlinks
    are followed only when their resolved targets remain inside the resolved
    root directory. The explicitly selected root is always resolved, even if
    it is a symlink. Upload filenames preserve the
    original paths, including aliases. Directory links are traversed only when
    recursive selection is enabled; links to ancestor directories are rejected.
    Only regular files are selected. The caller owns the returned streams.

    Args:
        dir_path: The path to the root directory to search for files.
        recursive: If True, search for files recursively in subdirectories.
            Defaults to False.
        include_pattern: A string or compiled regular expression pattern to use to
            filter files by name. If None, then all files are included. Defaults to
            None.
        follow_symlinks: If True, follow file and directory symlinks whose targets
            remain inside the root directory. Directory symlinks also require
            recursive selection. Defaults to False.

    Returns:
        A list of DioptraFile objects representing the selected files.

    Raises:
        FileNotFoundError: If the specified `dir_path` does not exist.
        NotADirectoryError: If `dir_path` is not a directory.
        ValueError: If a selected path escapes the root or contains a symlink cycle.
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

    root_dir = root_dir.resolve(strict=True)

    # If provided, ensure that the include_pattern regular expression is compiled
    if include_pattern is not None:
        include_pattern = re.compile(include_pattern)

    dioptra_files: list[DioptraFile] = []

    with ExitStack() as streams:
        for relative_path, target in _iter_selected_files(
            root_dir, recursive, include_pattern, follow_symlinks
        ):
            stream = streams.enter_context(target.open("rb"))
            dioptra_files.append(
                DioptraFile(
                    filename=relative_path.as_posix(),
                    stream=stream,
                    content_type=None,
                )
            )
        streams.pop_all()  # Transfer stream ownership only after complete selection.

    return dioptra_files


def _iter_selected_files(
    root: Path,
    recursive: bool,
    include_pattern: re.Pattern | None,
    follow_symlinks: bool,
) -> Iterator[tuple[Path, Path]]:
    """Yield logical paths and contained targets, detecting cycles per ancestry."""

    def visit(
        directory: Path, relative_dir: Path, ancestors: set[Path]
    ) -> Iterator[tuple[Path, Path]]:
        # The root and all directory targets are already resolved.
        if directory in ancestors:
            raise ValueError(f"Directory symlink cycle: {relative_dir}")

        ancestors = ancestors | {directory}

        for entry in directory.iterdir():
            if not follow_symlinks and entry.is_symlink():
                continue

            relative_path = relative_dir / entry.name

            # Preserve filename filtering and nonrecursive directory skipping.
            is_directory = entry.is_dir()
            if is_directory:
                if not recursive:
                    continue
            elif include_pattern is not None and not include_pattern.match(entry.name):
                continue

            try:
                target = entry.resolve(strict=True)
            except RuntimeError as err:
                raise ValueError(f"Symlink cycle: {relative_path}") from err

            if not target.is_relative_to(root):
                raise ValueError(
                    f"Selected path escapes root directory: {relative_path}"
                )

            if is_directory:
                yield from visit(target, relative_path, ancestors)
            elif target.is_file():
                yield relative_path, target

    yield from visit(root, Path(), set())


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


def delimited_values(
    kv_dict: dict[str, str] | None, equality: str = ":", separator: str = ","
) -> str:
    """Converts a dictionary to a string representing that dictionary.

    Args:
        kv_dict: The dictionary to convert.
        equality: The character to use to represent mappings (between keys and values in the dictionary).
        separator: The character to use to separate mappings.

    Returns:
        A string representing the dictionary.

    """

    kv_dict = kv_dict or {}
    return separator.join([f"{k}{equality}{v}" for k, v in kv_dict.items()])
