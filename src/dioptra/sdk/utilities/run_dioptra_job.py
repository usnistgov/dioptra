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

import argparse
import json
import os
import tarfile
from pathlib import Path, PurePosixPath
from typing import Any, Final, Iterable, Mapping, MutableMapping, cast

import mlflow
import structlog
import yaml
from structlog.stdlib import BoundLogger

from dioptra.client import DioptraClient, connect_json_dioptra_client
from dioptra.client.base import StatusCodeError
from dioptra.client.utils import FileTypes
from dioptra.sdk.api.artifact import ArtifactTaskInterface
from dioptra.sdk.utilities.contexts import import_temp
from dioptra.task_engine.issues import IssueSeverity
from dioptra.task_engine.task_engine import (
    ArtifactOutputEntry,
    ArtifactTaskEntry,
    run_experiment,
)
from dioptra.task_engine.validation import SCHEMA_FILENAME, get_json_schema, validate

LOGGER: BoundLogger = structlog.stdlib.get_logger()

DIOPTRA_JOB_ID: Final[str] = "dioptra.jobId"
ENV_DIOPTRA_API: Final[str] = "DIOPTRA_API"
ENV_DIOPTRA_WORKER_USERNAME: Final[str] = "DIOPTRA_WORKER_USERNAME"
ENV_DIOPTRA_WORKER_PASSWORD: Final[str] = "DIOPTRA_WORKER_PASSWORD"
ENV_MLFLOW_S3_ENDPOINT_URL: Final[str] = "MLFLOW_S3_ENDPOINT_URL"


class Context(object):
    def __init__(self) -> None:
        self.working_dir = Path().resolve()
        self.dioptra_dir = self.working_dir / ".dioptra"
        self.serialize_dir = self.dioptra_dir / "serialize"
        self.deserialize_dir = self.dioptra_dir / "deserialize"
        self.plugins_dir = self.dioptra_dir / "plugins"
        self.artifacts_dir = self.dioptra_dir / "artifacts"

        self.parameters_file = self.working_dir / "parameters.json"
        self.artifact_parameters_file = self.working_dir / "artifact_parameters.json"
        self.args_file = self.dioptra_dir / "args.json"
        self.artifacts_results_file = self.dioptra_dir / "artifacts.json"
        self.artifact_plugins_file = self.serialize_dir / "artifact_plugins.json"
        self.artifact_tasks_file = self.serialize_dir / "artifact_tasks.json"

    def yaml_path(self, entrypoint_name: str) -> Path:
        return Path(self.working_dir, f"{entrypoint_name}.yml")

    def mkdirs(self) -> None:
        # make the directories if needed
        self.dioptra_dir.mkdir(exist_ok=True)
        self.serialize_dir.mkdir(exist_ok=True)
        self.deserialize_dir.mkdir(exist_ok=True)
        self.plugins_dir.mkdir(exist_ok=True)
        self.artifacts_dir.mkdir(exist_ok=True)


def standalone() -> None:
    # Running the file as standalone does not enable the Mlflow Tracking or Dioptra
    # client capability. This is useful for debugging whether the job YAML and plugins
    # are set up appropriately.
    context = Context()
    if not context.args_file.exists():
        print(
            "Failed to locate arguments file for a standalone run. "
            "Is the environment correctly set-up for a run?"
        )
        exit(1)

    args = _load_json(context.args_file)
    job_id: int = args["job_id"]
    experiment_id: int = args["experiment_id"]
    entrypoint_name: str = args["entrypoint_name"]

    log = LOGGER.new(job_id=job_id, experiment_id=experiment_id)

    job_yaml = _load_job_yaml(context.yaml_path(entrypoint_name))
    _validate_yaml(job_yaml, log)
    _run_job(
        context=context,
        job_parameters=_load_json(context.parameters_file),
        job_yaml=job_yaml,
        artifact_parameters=_load_json(context.artifact_parameters_file),
        artifact_tasks=_build_artifact_tasks(
            context=context, plugins=_load_json(context.artifact_plugins_file), log=log
        ),
        log=log,
    )


def main(
    job_id: int,
    experiment_id: int,
    logger: BoundLogger | None = None,
) -> None:
    log = logger or LOGGER.new(job_id=job_id, experiment_id=experiment_id)  # noqa: F841
    context = Context()

    context.mkdirs()

    # obtain a connection to the dioptra REST API
    dioptra_client = _get_client(log)

    try:
        # Set Dioptra Job status to "started"
        dioptra_client.experiments.jobs.set_status(
            experiment_id=experiment_id, job_id=job_id, status="started"
        )
    except StatusCodeError:
        log.error(
            "Error while attempting to set status to Started. "
            "Is the job in a Queued status?"
        )
        exit(1)

    job_response = dioptra_client.jobs.get_by_id(job_id=job_id)
    group_id = job_response["group"]["id"]
    entrypoint_id = job_response["entrypoint"]["id"]
    entrypoint_snapshot_id = job_response["entrypoint"]["snapshotId"]
    entrypoint_name = job_response["entrypoint"]["name"]

    try:
        _validate_environment(log)

        # get and save out the yaml
        job_yaml = dioptra_client.entrypoints.snapshots.get_config(
            entrypoint_id=entrypoint_id, entrypoint_snapshot_id=entrypoint_snapshot_id
        )
        _save_job_yaml(filepath=context.yaml_path(entrypoint_name), job_yaml=job_yaml)

        # download artifact plugins
        serialize_plugins = (
            dioptra_client.entrypoints.snapshots.get_artifact_plugins_bundle(
                entrypoint_id=entrypoint_id,
                entrypoint_snapshot_id=entrypoint_snapshot_id,
                file_type=FileTypes.TAR_GZ,
                output_dir=context.dioptra_dir,
                file_stem="serialize",
            )
        )
        _unpack(serialize_plugins, context.serialize_dir, log)

        # create the final engine schema based on the artifact serialize plugins
        # TODO: fix this cast when client is fixed
        artifact_plugins: list[dict[str, Any]] = cast(
            list[dict[str, Any]],
            dioptra_client.entrypoints.snapshots.get_artifact_plugins(
                entrypoint_id=entrypoint_id,
                entrypoint_snapshot_id=entrypoint_snapshot_id,
            ),
        )

        _save_as_json(context.artifact_plugins_file, params=artifact_plugins)
        _create_engine_schema(context=context, plugins=artifact_plugins, log=log)
        _validate_yaml(job_yaml, log)

        # now download plugin-ins
        plugins = dioptra_client.entrypoints.snapshots.get_plugins_bundle(
            entrypoint_id=entrypoint_id,
            entrypoint_snapshot_id=entrypoint_snapshot_id,
            file_type=FileTypes.TAR_GZ,
            output_dir=context.dioptra_dir,
            file_stem="plugins",
        )
        _unpack(plugins, context.plugins_dir, log)

        # download each artifact parameter and its task plugin
        artifact_params = _download_artifacts(
            job_id=job_id, context=context, dioptra_client=dioptra_client, log=log
        )

        # get and save out the parameters
        job_parameters = dioptra_client.jobs.get_parameters(job_id=job_id)
        _save_as_json(context.parameters_file, job_parameters)

        # save out the arguments for potential later use
        _save_args(
            context.args_file,
            job_id=job_id,
            experiment_id=experiment_id,
            entrypoint_name=entrypoint_name,
        )

        _run_tracked_job(
            group_id=group_id,
            job_id=job_id,
            entrypoint_name=entrypoint_name,
            dioptra_client=dioptra_client,
            context=context,
            job_yaml=job_yaml,
            job_parameters=job_parameters,
            artifact_parameters=artifact_params,
            artifact_tasks=_build_artifact_tasks(
                context=context, plugins=artifact_plugins, log=log
            ),
            logger=log,
        )
    except Exception as e:
        log.exception("Job failed.")
        dioptra_client.experiments.jobs.set_status(
            experiment_id=experiment_id, job_id=job_id, status="failed"
        )
        raise e

    dioptra_client.experiments.jobs.set_status(
        experiment_id=experiment_id, job_id=job_id, status="finished"
    )


def _get_client(log: BoundLogger) -> DioptraClient[dict[str, Any]]:
    import logging

    logging.basicConfig(level=logging.DEBUG)
    if (username := os.getenv(ENV_DIOPTRA_WORKER_USERNAME)) is None:
        log.error(f"{ENV_DIOPTRA_WORKER_USERNAME} environment variable is not set")
        raise ValueError(
            f"{ENV_DIOPTRA_WORKER_USERNAME} environment variable is not set"
        )

    if (password := os.getenv(ENV_DIOPTRA_WORKER_PASSWORD)) is None:
        log.error(f"{ENV_DIOPTRA_WORKER_PASSWORD} environment variable is not set")
        raise ValueError(
            f"{ENV_DIOPTRA_WORKER_PASSWORD} environment variable is not set"
        )

    # Instantiate a Dioptra client and login using worker's authentication details
    try:
        client = connect_json_dioptra_client()

    except ValueError:
        log.error(f"{ENV_DIOPTRA_API} environment variable is not set")
        raise ValueError(f"{ENV_DIOPTRA_API} environment variable is not set") from None

    client.auth.login(username=username, password=password)

    return client


def _validate_environment(log: BoundLogger) -> None:
    if os.getenv(ENV_MLFLOW_S3_ENDPOINT_URL) is None:
        message = f"{ENV_MLFLOW_S3_ENDPOINT_URL} environment variable is not set"
        log.error(message)
        raise ValueError(message)


def _download_artifacts(
    job_id: int,
    context: Context,
    dioptra_client: DioptraClient[dict[str, Any]],
    log: BoundLogger,
) -> dict[str, Any]:
    artifact_params = dioptra_client.jobs.get_artifact_parameters(job_id=job_id)
    _save_as_json(context.artifact_parameters_file, artifact_params)
    for artifact in artifact_params.values():
        # download each artifact
        artifact_name = f"{artifact['artifact_id']}_{artifact['artifact_snapshot_id']}"
        if artifact["is_dir"]:
            bundle = dioptra_client.artifacts.snapshots.get_contents(
                artifact_id=artifact["artifact_id"],
                artifact_snapshot_id=artifact["artifact_snapshot_id"],
                file_type=FileTypes.TAR_GZ,
                file_stem=artifact_name,
                output_dir=context.dioptra_dir,
            )
            _unpack(bundle, context.artifacts_dir / artifact_name, log)
        else:
            dioptra_client.artifacts.snapshots.get_contents(
                artifact_id=artifact["artifact_id"],
                artifact_snapshot_id=artifact["artifact_snapshot_id"],
                file_stem=artifact_name,
                output_dir=context.artifacts_dir,
            )

        # now download the artifact task handlers
        plugin_id = artifact["artifact_task"]["plugin_id"]
        plugin_snapshot_id = artifact["artifact_task"]["plugin_snapshot_id"]
        plugin_name = artifact["artifact_task"]["plugin_name"]
        task_plugin_name = f"{plugin_id}_{plugin_snapshot_id}"
        if not (context.deserialize_dir / task_plugin_name).exists():
            bundle = dioptra_client.plugins.snapshots.get_files_bundle(
                plugin_id=plugin_id,
                plugin_snapshot_id=plugin_snapshot_id,
                file_type=FileTypes.TAR_GZ,
                output_dir=context.deserialize_dir,
                file_stem=task_plugin_name,
            )
            _unpack(bundle, context.deserialize_dir, log)
            original = Path(context.deserialize_dir, plugin_name)
            original.rename(Path(context.deserialize_dir, task_plugin_name))

    return artifact_params


def _register_artifacts(
    group_id: int,
    job_id: int,
    dioptra_client: DioptraClient[dict[str, Any]],
    artifact_results_file: Path,
) -> None:
    # load up the artifacts.json file
    artifacts: list[ArtifactOutputEntry] = []
    if artifact_results_file.exists():
        artifacts = cast(
            list[ArtifactOutputEntry],
            _load_json(filepath=artifact_results_file).get("artifacts", []),
        )
    for artifact in artifacts:
        artifact_path_name = PurePosixPath(artifact["path"]).name
        # add artifact to mlflow
        mlflow.log_artifact(local_path=artifact["path"], artifact_path=artifact["name"])
        uri = mlflow.get_artifact_uri(f"{artifact['name']}/{artifact_path_name}")
        # add artifact to dioptra_client
        dioptra_client.artifacts.create(
            group_id=group_id,
            job_id=job_id,
            artifact_uri=uri,
            plugin_snapshot_id=artifact["task_plugin_snapshot_id"],
            task_id=artifact["task_id"],
            description=(
                f"Artifact, {artifact['name']}, generated and stored as part of job, "
                f"{job_id}"
            ),
        )


def _run_job(
    context: Context,
    job_yaml: Mapping[str, Any],
    job_parameters: MutableMapping[str, Any],
    artifact_parameters: MutableMapping[str, Any],
    artifact_tasks: dict[str, ArtifactTaskEntry],
    log: BoundLogger,
) -> None:
    """Run the job.

    Args:
        plugins_dir: Path to the plugins directory
        job_yaml: A declarative experiment description, as a mapping
        job_parameters: Global parameters for this run, as a mapping from
            parameter name to value
        logger: A structlog logger instance. If not provided, a new logger
            will be created
    """
    try:
        run_experiment(
            experiment_desc=job_yaml,
            global_parameters=job_parameters,
            artifact_parameters=artifact_parameters,
            artifact_tasks=artifact_tasks,
            artifacts_dir=context.artifacts_dir,
            plugins_dir=context.plugins_dir,
            serialize_dir=context.serialize_dir,
            deserialize_dir=context.deserialize_dir,
        )

        log.info("=== Run succeeded ===")

    except Exception as e:
        log.exception("=== Run failed ===")
        raise e


def _run_tracked_job(
    group_id: int,
    job_id: int,
    entrypoint_name: str,
    dioptra_client: DioptraClient[dict[str, Any]],
    context: Context,
    job_yaml: Mapping[str, Any],
    job_parameters: MutableMapping[str, Any],
    artifact_parameters: MutableMapping[str, Any],
    artifact_tasks: dict[str, ArtifactTaskEntry],
    logger: BoundLogger,
) -> None:
    """Run the job and start tracking the run in MLflow tracking server.

    Args:
        dioptra_client: A client for interacting with the Dioptra service.
        plugins_dir: Path to the plugins directory
        job_yaml: A declarative experiment description, as a mapping
        job_parameters: Global parameters for this run, as a mapping from
            parameter name to value
        logger: A structlog logger instance. If not provided, a new logger
            will be created
    """
    active_run = mlflow.start_run()

    try:
        dioptra_client.jobs.set_mlflow_run_id(
            job_id=job_id, mlflow_run_id=active_run.info.run_id
        )
        mlflow.set_tag(DIOPTRA_JOB_ID, job_id)
        mlflow.log_dict(cast(dict[str, Any], job_yaml), entrypoint_name)
        mlflow.log_params(cast(dict[str, Any], job_parameters))

        run_experiment(
            experiment_desc=job_yaml,
            global_parameters=job_parameters,
            artifact_parameters=artifact_parameters,
            artifact_tasks=artifact_tasks,
            artifacts_dir=context.artifacts_dir,
            plugins_dir=context.plugins_dir,
            serialize_dir=context.serialize_dir,
            deserialize_dir=context.deserialize_dir,
        )
        _register_artifacts(
            group_id=group_id,
            job_id=job_id,
            dioptra_client=dioptra_client,
            artifact_results_file=context.artifacts_results_file,
        )
        logger.info("=== Run succeeded ===")
        mlflow.end_run()

    except Exception as e:
        logger.exception("=== Run failed ===")
        mlflow.end_run("FAILED")
        raise e


def _build_artifact_tasks(
    context: Context, plugins: Iterable[dict[str, Any]], log: BoundLogger
) -> dict[str, ArtifactTaskEntry]:
    result: dict[str, ArtifactTaskEntry] = {}

    # run through the artifact plugins
    for plugin in plugins:
        plugin_name: str = plugin["name"]
        for file in plugin["files"]:
            filename = Path(file["filename"]).stem
            # only temporarily import - might clash with deserialization
            with import_temp(
                f"{plugin_name}.{filename}", context.serialize_dir
            ) as plugin_file:
                for artifact_task in file["tasks"]["artifacts"]:
                    task = getattr(plugin_file, artifact_task["name"], None)
                    if task is None:
                        log.error(
                            f"Failed to locate artifact task: {artifact_task['name']}"
                        )
                        exit(1)
                    if issubclass(task, ArtifactTaskInterface):
                        result[task.name()] = ArtifactTaskEntry(
                            task=task,
                            plugin_snapshot_id=plugin["snapshotId"],
                            task_id=artifact_task["id"],
                        )
    return result


def _create_engine_schema(
    context: Context, plugins: Iterable[dict[str, Any]], log: BoundLogger
) -> None:
    task_names = []
    allof = []
    # run through the artifact plugins
    for plugin in plugins:
        plugin_name: str = plugin["name"]
        for file in plugin["files"]:
            filename = Path(file["filename"]).stem
            # only temporarily import - might clash with deserialization
            with import_temp(
                f"{plugin_name}.{filename}", context.serialize_dir
            ) as plugin_file:
                for artifact_task in file["tasks"]["artifacts"]:
                    task = getattr(plugin_file, artifact_task["name"], None)
                    if task is None:
                        log.error(
                            f"Failed to locate artifact task: {artifact_task['name']}"
                        )
                        exit(1)
                    if issubclass(task, ArtifactTaskInterface):
                        task_names.append(task.name())
                        validation = task.validation()
                        if validation is not None:
                            allof.append(
                                {
                                    "if": {
                                        "properties": {"name": {"const": task.name()}}
                                    },
                                    "then": {
                                        "properties": {
                                            "args": {"properties": validation}
                                        }
                                    },
                                }
                            )
    # create final validation schema
    engine_schema = get_json_schema(default=True)
    engine_schema["$defs"]["artifact_task"]["properties"]["name"]["enum"] = task_names
    engine_schema["$defs"]["artifact_task"]["allOf"] = allof
    _save_as_json(filepath=context.dioptra_dir / SCHEMA_FILENAME, params=engine_schema)


def _save_job_yaml(filepath: Path, job_yaml: Mapping[str, Any]) -> None:
    with filepath.open("wt") as f:
        yaml.safe_dump(data=job_yaml, stream=f)


def _load_job_yaml(filepath: Path) -> Mapping[str, Any]:
    with filepath.open("rt") as f:
        return cast(Mapping[str, Any], yaml.safe_load(f))


def _save_as_json(filepath: Path, params: Any) -> None:
    with filepath.open("wt") as f:
        json.dump(obj=params, fp=f)


def _load_json(filepath: Path) -> Any:
    with filepath.open("rt") as f:
        return json.load(f)


def _unpack(source: Path, dest: Path, log: BoundLogger) -> None:
    # Unpack the (trusted) tar.gz file
    try:
        with tarfile.open(source, mode="r:*") as tar:
            tar.extractall(path=dest, filter="data")
    except Exception as e:
        log.exception(f"Could not extract from tar file {source.as_posix()}")
        raise e


def _save_args(
    filepath: Path, job_id: int, experiment_id: int, entrypoint_name: str
) -> None:
    _save_as_json(
        filepath=filepath,
        params={
            "job_id": job_id,
            "experiment_id": experiment_id,
            "entrypoint_name": entrypoint_name,
        },
    )


def _validate_yaml(
    job_yaml: Mapping[str, Any],
    log: BoundLogger,
) -> None:
    issues = validate(job_yaml)
    errors: list[str] = []

    for issue in issues:
        if issue.severity is IssueSeverity.WARNING:
            log.warn("Found issue with Job YAML", message=issue.message)

        if issue.severity is IssueSeverity.ERROR:
            log.error("Found error in Job YAML", message=issue.message)
            errors.append(issue.message)

    if errors:
        raise ValueError(f"Errors found in Job YAML: {errors}")


def _parse_args() -> argparse.Namespace:
    """
    Set up and parse commandline parameters.
    """
    arg_parser = argparse.ArgumentParser(
        description="Start a Dioptra Job",
    )

    subparsers = arg_parser.add_subparsers(help="subcommand help")

    # standalone
    stand_parser = subparsers.add_parser("standalone", help="run standalone")
    stand_parser.set_defaults(func=standalone)

    # connected
    connected_parser = subparsers.add_parser(
        "connected",
        help="run as connected",
    )
    connected_parser.set_defaults(
        func=lambda args: main(experiment_id=args.experiment_id, job_id=args.job_id)
    )

    connected_parser.add_argument(
        "experiment_id",
        type=int,
        help="The ID of the experiment containing the job.",
    )

    connected_parser.add_argument(
        "job_id",
        type=int,
        help="The Job ID to process.",
    )
    return arg_parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    args.func(args)
