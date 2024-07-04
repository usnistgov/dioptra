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
import json
from pathlib import Path
from typing import Final

import structlog
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models

LOGGER: BoundLogger = structlog.stdlib.get_logger()

FLOAT_PARAM_TYPE: Final[str] = "float"
JSON_FILE_ENCODING: Final[str] = "utf-8"


def export_job_parameters(
    job_param_values: list[models.EntryPointParameterValue],
    base_dir: Path,
    logger: BoundLogger | None = None,
) -> Path:
    """Export a job's parameters to a parameters.json file in a specified directory.

    Args:
        base_dir: The directory to export the parameters JSON file to.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The path to the exported parameters.json file.
    """
    log = logger or LOGGER.new()  # noqa: F841
    job_params_json_path = Path(base_dir, "parameters").with_suffix(".json")

    job_parameters: dict[str, str | int | float | None] = {}
    for param_value in job_param_values:
        if param_value.parameter.parameter_type == FLOAT_PARAM_TYPE:
            job_parameters[param_value.parameter.name] = _convert_to_number(
                param_value.value
            )

        else:
            job_parameters[param_value.parameter.name] = param_value.value

    with job_params_json_path.open("wt", encoding=JSON_FILE_ENCODING) as f:
        json.dump(job_parameters, f, indent=2)

    return job_params_json_path


def _convert_to_number(number: str | None) -> int | float | None:
    if number is None:
        return None

    if number.isnumeric():
        return int(number)

    return float(number)
