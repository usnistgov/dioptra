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
"""A set of shared utility classes and functions.

Classes:
    RichConsole: A simple API for printing formatted text in the terminal.

Functions:
    make_tar: Archive a list of directories and files.
"""
from __future__ import annotations

import os
import tarfile
from pathlib import Path

from rich.console import Console
from rich.panel import Panel


class RichConsole(object):
    """A simple API for printing formatted text in the terminal.

    Args:
        console: A rich.console.Console object.
    """

    def __init__(self, console: Console) -> None:
        self._console = console

    def print_alert(self, text: str) -> None:
        """Print an alert message.

        Args:
            text: The text to print.
        """
        content: str = f":heavy_exclamation_mark: {text}"
        self._console.print(content)

    def print_failure(self, text: str) -> None:
        """Print a failure message.

        Args:
            text: The text to print.
        """
        content: str = f":x:  {text}"
        self._console.print(content)

    def print_info(self, text: str) -> None:
        """Print an informational message.

        Args:
            text: The text to print.
        """
        content: str = f"[bold yellow]Ⓘ[/bold yellow]  {text}"
        self._console.print(content)

    def print_parameter(self, name: str, value: str) -> None:
        """Print a parameter name and its value.

        Args:
            name: The name of the parameter.
            value: The value of the parameter.
        """
        content: str = f" ‣ [bold]{name}:[/bold] {value}"
        self._console.print(content)

    def print_success(self, text: str) -> None:
        """Print a success message.

        Args:
            text: The text to print.
        """
        content: str = f" [bold bright_green]✔[/bold bright_green] {text}"
        self._console.print(content)

    def print_title(self, text: str) -> None:
        """Print a title.

        Args:
            text: The text to print.
        """
        content: Panel = Panel(renderable=text, expand=False)
        self._console.print(content, style="bold cyan")

    def print_warning(self, text: str) -> None:
        """Print a warning message.

        Args:
            text: The text to print.
        """
        content: str = f":warning: {text}"
        self._console.print(content)


def make_tar(
    source_dir: list[str | Path],
    tarball_filename: str,
    tarball_write_mode: str = "w:gz",
    working_dir: str | Path | None = None,
) -> Path:
    """Archive a list of directories and files.

    This implementation flattens the source directory structure so that all the files
    are placed in the root of the archive, and then the archive is compressed.

    Args:
        source_dir: The directories and files which should be archived.
        tarball_filename: The filename to use for the archived tarball.
        tarball_write_mode: The write mode for the tarball, see :py:func:`tarfile.open`
            for the full list of compression options. The default is `"w:gz"` (gzip
            compression).
        working_dir: The location where the file should be saved. If `None`, then the
            current working directory is used. The default is `None`.

    Returns:
        Path to the archive.

    See Also:
        - :py:func:`tarfile.open`
    """
    if working_dir is None:
        working_dir = Path.cwd()

    working_dir = Path(working_dir)
    tarball_path = working_dir / tarball_filename

    with tarfile.open(tarball_path, tarball_write_mode) as f:
        for dir in source_dir:
            dir = Path(dir)
            if dir.is_dir():
                for dirpath, _, filenames in os.walk(dir):
                    for name in filenames:
                        name = Path(dirpath, name)
                        f.add(name, name.name)
            else:
                f.add(dir, dir.name)

    return tarball_path
