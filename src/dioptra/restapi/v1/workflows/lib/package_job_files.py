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
import tarfile
import zipfile
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import IO

import structlog
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models

from ..schema import FileTypes
from .export_job_parameters import export_job_parameters
from .export_plugin_files import export_plugin_files
from .export_run_dioptra_job_script import export_run_dioptra_job_script
from .export_task_engine_yaml import export_task_engine_yaml

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def package_job_files(
    job_id: int,
    experiment: models.Experiment,
    entry_point: models.EntryPoint,
    entry_point_plugin_files: list[models.EntryPointPluginFile],
    job_parameter_values: list[models.EntryPointParameterValue],
    file_type: FileTypes,
    logger: BoundLogger | None = None,
) -> IO[bytes]:
    """Package the job files into a named temporary file.

    Args:
        job_id: The ID of the job to package the files for.
        experiment: The experiment the job is associated with.
        entry_point: The job's entrypoint.
        entry_point_plugin_files: The job's entrypoint plugin files.
        job_parameter_values: The job's assigned parameter values.
        file_type: The type of file to package the job files into.
        logger: A structlog logger object to use for logging. A new logger will be
            created if None.

    Returns:
        The packaged job files as a named temporary file.
    """
    log = logger or LOGGER.new()  # noqa: F841

    with TemporaryDirectory() as tmp_dir:
        base_dir = Path(tmp_dir)
        plugin_base_dir = base_dir / "plugins"

        _ = export_plugin_files(
            entry_point_plugin_files=entry_point_plugin_files,
            plugins_base_dir=plugin_base_dir,
            logger=log,
        )
        task_engine_yaml_path = export_task_engine_yaml(
            entrypoint=entry_point,
            entry_point_plugin_files=entry_point_plugin_files,
            base_dir=base_dir,
            logger=log,
        )
        job_params_json_path = export_job_parameters(
            job_param_values=job_parameter_values, base_dir=base_dir, logger=log
        )
        run_dioptra_job_script = export_run_dioptra_job_script(
            job_id=job_id,
            experiment_id=experiment.resource_id,
            task_engine_yaml_path=task_engine_yaml_path.name,
            job_params_json_path=job_params_json_path.name,
            base_dir=base_dir,
            logger=log,
        )

        if file_type == FileTypes.TAR_GZ:
            return _package_as_tarfile(
                plugin_base_dir=plugin_base_dir,
                task_engine_yaml_path=task_engine_yaml_path,
                job_params_json_path=job_params_json_path,
                script_path=run_dioptra_job_script,
                logger=log,
            )

        if file_type == FileTypes.ZIP:
            return _package_as_zipfile(
                plugin_base_dir=plugin_base_dir,
                task_engine_yaml_path=task_engine_yaml_path,
                job_params_json_path=job_params_json_path,
                script_path=run_dioptra_job_script,
                logger=log,
            )


def _package_as_tarfile(
    plugin_base_dir: Path,
    task_engine_yaml_path: Path,
    job_params_json_path: Path,
    script_path: Path,
    logger: BoundLogger | None = None,
) -> IO[bytes]:
    log = logger or LOGGER.new()  # noqa: F841

    package_file = NamedTemporaryFile(suffix=".tar.gz")
    with tarfile.open(fileobj=package_file, mode="w:gz") as tar:
        tar.add(str(plugin_base_dir), plugin_base_dir.name, recursive=True)
        tar.add(str(task_engine_yaml_path), task_engine_yaml_path.name, recursive=False)
        tar.add(str(job_params_json_path), job_params_json_path.name, recursive=False)
        tar.add(str(script_path), script_path.name, recursive=False)

    package_file.seek(0)
    return package_file


def _package_as_zipfile(
    plugin_base_dir: Path,
    task_engine_yaml_path: Path,
    job_params_json_path: Path,
    script_path: Path,
    logger: BoundLogger | None = None,
) -> IO[bytes]:
    log = logger or LOGGER.new()  # noqa: F841

    package_file = NamedTemporaryFile(suffix=".zip")
    with zipfile.ZipFile(package_file, "w") as zipf:
        for file in plugin_base_dir.rglob("*"):
            zipf.write(file, file.relative_to(plugin_base_dir))

        zipf.write(task_engine_yaml_path, task_engine_yaml_path.name)
        zipf.write(job_params_json_path, job_params_json_path.name)
        zipf.write(script_path, script_path.name)

    package_file.seek(0)
    return package_file
