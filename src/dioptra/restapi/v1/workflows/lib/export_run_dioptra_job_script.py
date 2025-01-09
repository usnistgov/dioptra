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
from string import Template
from typing import Final

import structlog
from structlog.stdlib import BoundLogger

from dioptra.restapi.utils import read_text_file

LOGGER: BoundLogger = structlog.stdlib.get_logger()

SCRIPT_FILE_ENCODING: Final[str] = "utf-8"
CURRENT_PACKAGE: Final[str] = "dioptra.restapi.v1.workflows.lib"
TEMPLATE_FILENAME: Final[str] = "run_dioptra_job.py.tmpl"


def export_run_dioptra_job_script(
    job_id: int,
    experiment_id: int,
    task_engine_yaml_path: str,
    job_params_json_path: str,
    base_dir: Path,
    logger: BoundLogger | None = None,
) -> Path:
    """Render and export the run_dioptra_job.py script to a specified directory.

    Args:
        base_dir: The directory to export the rendered script to.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The path to the exported script.
    """
    log = logger or LOGGER.new()  # noqa: F841
    script_path = Path(base_dir, "run_dioptra_job").with_suffix(".py")
    script = _render_run_dioptra_job_script(
        job_id=job_id,
        experiment_id=experiment_id,
        task_engine_yaml_path=task_engine_yaml_path,
        job_params_json_path=job_params_json_path,
    )

    with script_path.open("wt", encoding=SCRIPT_FILE_ENCODING) as f:
        f.write(script)

    return script_path


def _render_run_dioptra_job_script(
    job_id: int,
    experiment_id: int,
    task_engine_yaml_path: str,
    job_params_json_path: str,
):
    template_text = read_text_file(package=CURRENT_PACKAGE, filename=TEMPLATE_FILENAME)
    template = Template(template_text)

    return template.substitute(
        job_id=job_id,
        experiment_id=experiment_id,
        task_engine_yaml_path=task_engine_yaml_path,
        job_params_json_path=job_params_json_path,
    )
