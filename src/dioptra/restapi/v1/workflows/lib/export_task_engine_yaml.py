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
from typing import Any, Final

import structlog
from structlog.stdlib import BoundLogger

from .type_coercions import (
    BOOLEAN_PARAM_TYPE,
    FLOAT_PARAM_TYPE,
    INTEGER_PARAM_TYPE,
    STRING_PARAM_TYPE,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

EXPLICIT_GLOBAL_TYPES: Final[set[str]] = {
    STRING_PARAM_TYPE,
    BOOLEAN_PARAM_TYPE,
    INTEGER_PARAM_TYPE,
    FLOAT_PARAM_TYPE,
}
YAML_FILE_ENCODING: Final[str] = "utf-8"
YAML_EXPORT_SETTINGS: Final[dict[str, Any]] = {
    "indent": 2,
    "sort_keys": False,
    "encoding": YAML_FILE_ENCODING,
}


def export_task_engine_yaml(
    entry_point_name: str,
    task_engine_yaml: str,
    base_dir: Path,
    logger: BoundLogger | None = None,
) -> Path:
    """Export a task engine YAML file to a specified directory.

    Args:
        entry_point_name: The name of the entrypoint to export.
        task_engine_yaml: The task engine YAML file to export.
        base_dir: The directory to export the task engine YAML file to.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The path to the exported task engine YAML file.
    """
    log = logger or LOGGER.new()  # noqa: F841
    task_yaml_path = Path(base_dir, entry_point_name).with_suffix(".yml")

    with task_yaml_path.open("wt", encoding=YAML_FILE_ENCODING) as f:
        f.write(task_engine_yaml)

    return task_yaml_path
