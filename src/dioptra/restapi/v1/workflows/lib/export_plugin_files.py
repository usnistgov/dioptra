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
from pathlib import Path

import structlog
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def export_plugin_files(
    entry_point_plugin_files: list[models.EntryPointPluginFile],
    plugins_base_dir: Path,
    logger: BoundLogger | None = None,
) -> list[Path]:
    """Export an entrypoint's plugin files and folders in a specified directory.

    Args:
        entry_point_plugin_files: A list of entrypoint plugin files to be exported.
        plugins_base_dir: The base directory to save the plugin files and folders in.
        logger: A structlog logger object.

    Returns:
        A list of paths pointing to the exported plugin directories.
    """
    log = logger or LOGGER.new()  # noqa: F841
    plugin_dirs: set[Path] = set()

    for entry_point_plugin_file in entry_point_plugin_files:
        plugin = entry_point_plugin_file.plugin
        plugin_file = entry_point_plugin_file.plugin_file

        plugin_path = plugins_base_dir / plugin.name
        plugin_dirs.add(plugin_path)

        plugin_path.mkdir(parents=True, exist_ok=True)
        (plugin_path / plugin_file.filename).parent.mkdir(parents=True, exist_ok=True)
        (plugin_path / plugin_file.filename).write_text(plugin_file.contents or "")

    return list(plugin_dirs)
