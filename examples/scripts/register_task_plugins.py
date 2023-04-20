#!/usr/bin/env python
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
"""Register the custom task plugins used in Dioptra's examples and demos.

Classes:
    CustomTaskPlugin: A dictionary containing the name and path to the tarball for
        each custom task plugin package.

Functions:
    make_custom_plugins: Create a tarball for each custom task plugin package under a
        directory.
    register_task_plugins: The Click command for registering the custom task plugins
        used in Dioptra's examples and demos.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterable, TypedDict

import click
from rich.console import Console

# The try/except ImportError blocks allow this script to be invoked using:
#     python ./scripts/register_task_plugins.py  # OR
#     python -m scripts.register_task_plugins
try:
    from .client import DioptraClient

except ImportError:
    from client import DioptraClient

try:
    from .utils import RichConsole, make_tar

except ImportError:
    from utils import RichConsole, make_tar

_CONTEXT_SETTINGS = dict(
    help_option_names=["-h", "--help"],
    show_default=True,
)


class CustomTaskPlugin(TypedDict):
    name: str
    path: Path


def make_custom_plugins(
    plugins_dir: Path, output_dir: Path
) -> Iterable[CustomTaskPlugin]:
    """Create a tarball for each custom task plugin package under a directory.

    Args:
        plugins_dir: The directory containing the custom task plugin subdirectories.
        output_dir: The directory where the tarballs will be saved.

    Yields:
        A dictionary containing the name and path to the tarball for each custom task
        plugin package.
    """
    plugin_packages: list[Path] = [x for x in plugins_dir.glob("*/*") if x.is_dir()]

    for plugin_package in plugin_packages:
        plugin_name = plugin_package.name
        plugin_path = make_tar(
            source_dir=[plugin_package],
            tarball_filename=f"custom-plugins-{plugin_name}.tar.gz",
            working_dir=output_dir,
        )
        yield CustomTaskPlugin(name=plugin_name, path=plugin_path)


@click.command(context_settings=_CONTEXT_SETTINGS)
@click.option(
    "--plugins-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default="./task-plugins",
    help=(
        "The path to the directory containing the custom task plugin subdirectories."
    ),
)
@click.option(
    "--api-url",
    type=click.STRING,
    default="http://localhost",
    help="The url to the Dioptra REST API.",
)
def register_task_plugins(plugins_dir, api_url):
    """Register the custom task plugins used in Dioptra's examples and demos."""

    console = RichConsole(Console())
    client = DioptraClient(address=api_url)

    console.print_title("Dioptra Examples - Register Custom Task Plugins")
    console.print_parameter("plugins_dir", value=click.format_filename(plugins_dir))
    console.print_parameter("api_url", value=f"[default not bold]{api_url}[/]")

    with TemporaryDirectory() as temp_dir:
        custom_plugins = make_custom_plugins(
            plugins_dir=plugins_dir, output_dir=Path(temp_dir)
        )

        for custom_plugin in custom_plugins:
            response = client.get_custom_task_plugin(name=custom_plugin["name"])

            if response is None or "Not Found" in response.get("message", []):
                response = client.upload_custom_plugin_package(
                    custom_plugin_name=custom_plugin["name"],
                    custom_plugin_file=custom_plugin["path"],
                )
                response_after = client.get_custom_task_plugin(
                    name=custom_plugin["name"]
                )

                if response_after is None or "Not Found" in response_after.get(
                    "message", []
                ):
                    raise RuntimeError(
                        "Failed to register the custom task plugin "
                        f"{custom_plugin['name']!r}. Is the API URL correct?"
                    )

                console.print_success(
                    "[bold green]Success![/] [default not bold]Registered the custom "
                    f"task plugin {custom_plugin['name']!r}.[/]"
                )

            else:
                console.print_info(
                    "[bold white]Skipped.[/] [default not bold]The custom task plugin "
                    f"{custom_plugin['name']!r} is already registered.[/]"
                )

    console.print_success(
        "[default no bold]Custom task plugin registration is complete.[/]"
    )


if __name__ == "__main__":
    register_task_plugins()
