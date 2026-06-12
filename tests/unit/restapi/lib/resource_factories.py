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
from __future__ import annotations

import datetime
from typing import Any

import dioptra.restapi.db.models as models


def make_queue(account: Any, fake_data: Any, db_session: Any) -> models.Queue:
    return fake_data.queue(account.user, account.group)


def make_queue_snapshot(
    source_queue: models.ResourceSnapshot, hours_offset: int = 1
) -> models.Queue:
    queue = _assert_snapshot_type(source_queue, models.Queue)
    snapshot = models.Queue(
        queue.description,
        queue.resource,
        queue.creator,
        f"{queue.name}-updated",
    )
    snapshot.created_on = queue.created_on + datetime.timedelta(hours=hours_offset)
    return snapshot


def make_wrong_resource_type_queue(
    account: Any, fake_data: Any, db_session: Any
) -> models.Queue:
    resource = models.Resource("experiment", account.group)
    return models.Queue("description", resource, account.user, "wrong type queue")


def make_type(
    account: Any, fake_data: Any, db_session: Any
) -> models.PluginTaskParameterType:
    return fake_data.plugin_task_parameter_type(
        account.user, account.group, name="contract_type"
    )


def make_type_snapshot(
    source_type: models.ResourceSnapshot, hours_offset: int = 1
) -> models.PluginTaskParameterType:
    type_ = _assert_snapshot_type(source_type, models.PluginTaskParameterType)
    snapshot = models.PluginTaskParameterType(
        type_.description,
        type_.resource,
        type_.creator,
        f"{type_.name}_updated",
        type_.structure,
    )
    snapshot.created_on = type_.created_on + datetime.timedelta(hours=hours_offset)
    return snapshot


def make_wrong_resource_type_type(
    account: Any, fake_data: Any, db_session: Any
) -> models.PluginTaskParameterType:
    resource = models.Resource("queue", account.group)
    return models.PluginTaskParameterType(
        "description",
        resource,
        account.user,
        "wrong_type_contract_type",
        None,
    )


def make_experiment(account: Any, fake_data: Any, db_session: Any) -> models.Experiment:
    return fake_data.experiment(account.user, account.group)


def make_experiment_snapshot(
    source_experiment: models.ResourceSnapshot, hours_offset: int = 1
) -> models.Experiment:
    experiment = _assert_snapshot_type(source_experiment, models.Experiment)
    snapshot = models.Experiment(
        name=f"{experiment.name}_updated",
        description=experiment.description,
        resource=experiment.resource,
        creator=experiment.creator,
    )
    snapshot.created_on = experiment.created_on + datetime.timedelta(
        hours=hours_offset
    )
    return snapshot


def make_wrong_resource_type_experiment(
    account: Any, fake_data: Any, db_session: Any
) -> models.Experiment:
    resource = models.Resource("queue", account.group)
    return models.Experiment(
        name="wrong_type_experiment",
        description="description",
        resource=resource,
        creator=account.user,
    )


def make_entrypoint(
    creator: models.User,
    group: models.Group,
    name: str = "test_ep",
    description: str = "",
    task_graph: str = "graph:",
    artifact_graph: str = "artifact_output:",
) -> models.EntryPoint:
    """Create a basic EntryPoint without children."""
    ep_resource = models.Resource("entry_point", group)
    return models.EntryPoint(
        description=description,
        resource=ep_resource,
        creator=creator,
        name=name,
        task_graph=task_graph,
        artifact_graph=artifact_graph,
        parameters=[],
        artifact_parameters=[],
    )


def make_entrypoint_for_contract(
    account: Any, fake_data: Any, db_session: Any
) -> models.EntryPoint:
    return make_entrypoint(account.user, account.group)


def make_entrypoint_snapshot(
    source_ep: models.ResourceSnapshot, hours_offset: int = 1
) -> models.EntryPoint:
    """Create a new EntryPoint snapshot based on an existing entrypoint."""
    entrypoint = _assert_snapshot_type(source_ep, models.EntryPoint)
    snapshot = models.EntryPoint(
        description=entrypoint.description,
        resource=entrypoint.resource,
        creator=entrypoint.creator,
        name=f"{entrypoint.name}_updated",
        task_graph=entrypoint.task_graph,
        artifact_graph=entrypoint.artifact_graph,
        parameters=[],
        artifact_parameters=[],
    )
    snapshot.created_on = entrypoint.created_on + datetime.timedelta(
        hours=hours_offset
    )
    return snapshot


def make_wrong_resource_type_entrypoint(
    account: Any, fake_data: Any, db_session: Any
) -> models.EntryPoint:
    resource = models.Resource("queue", account.group)
    return models.EntryPoint(
        name="wrong_type_entrypoint",
        task_graph="graph:",
        parameters=[],
        artifact_graph="",
        artifact_parameters=[],
        description="description",
        resource=resource,
        creator=account.user,
    )


def make_plugin(
    creator: models.User,
    group: models.Group,
    name: str = "test_plugin",
    description: str = "",
) -> models.Plugin:
    """Create a basic Plugin without dependencies."""
    plugin_resource = models.Resource("plugin", group)
    return models.Plugin(
        description=description,
        resource=plugin_resource,
        creator=creator,
        name=name,
    )


def make_job(
    creator: models.User,
    group: models.Group,
    experiment: models.Experiment,
    entry_point: models.EntryPoint,
    queue: models.Queue,
    timeout: str = "24h",
    status: str = "queued",
    description: str = "",
) -> models.Job:
    """Create a basic Job with required relationships."""
    job_resource = models.Resource("job", group)
    entry_point_parameter_values = [
        models.EntryPointParameterValue(
            value="test_value",
            job_resource=job_resource,
            parameter=entry_point.parameters[0] if entry_point.parameters else None,
        ),
    ]
    job = models.Job(
        timeout=timeout,
        status=status,
        description=description,
        resource=job_resource,
        creator=creator,
    )
    job.entry_point_job = models.EntryPointJob(
        job_resource=job_resource,
        entry_point=entry_point,
        entry_point_parameter_values=entry_point_parameter_values,
        entry_point_artifact_parameter_values=[],
    )
    job.experiment_job = models.ExperimentJob(
        job_resource=job_resource,
        experiment=experiment,
    )
    job.queue_job = models.QueueJob(
        job_resource=job_resource,
        queue=queue,
    )
    return job


def make_job_snapshot(
    source_job: models.ResourceSnapshot,
    hours_offset: int = 1,
    new_status: str | None = None,
) -> models.Job:
    """Create a new Job snapshot based on an existing job."""
    job = _assert_snapshot_type(source_job, models.Job)
    status = new_status if new_status is not None else job.status
    snapshot = models.Job(
        timeout=job.timeout,
        status=status,
        description=job.description,
        resource=job.resource,
        creator=job.creator,
    )
    snapshot.created_on = job.created_on + datetime.timedelta(hours=hours_offset)
    return snapshot


def make_artifact(
    creator: models.User,
    group: models.Group,
    job: models.Job,
    uri: str = "s3://test-bucket/test-artifact",
    is_dir: bool = False,
    file_size: int | None = None,
    description: str = "",
) -> models.Artifact:
    """Create a basic Artifact."""
    artifact_resource = models.Resource("artifact", group)
    artifact = models.Artifact(
        uri=uri,
        is_dir=is_dir,
        file_size=file_size,
        description=description,
        resource=artifact_resource,
        creator=creator,
    )
    job.children.append(artifact_resource)
    return artifact


def make_artifact_snapshot(
    source_artifact: models.ResourceSnapshot, hours_offset: int = 1
) -> models.Artifact:
    """Create a new Artifact snapshot based on an existing artifact."""
    artifact = _assert_snapshot_type(source_artifact, models.Artifact)
    snapshot = models.Artifact(
        uri=artifact.uri,
        is_dir=artifact.is_dir,
        file_size=artifact.file_size,
        description=artifact.description,
        resource=artifact.resource,
        creator=artifact.creator,
    )
    snapshot.created_on = artifact.created_on + datetime.timedelta(
        hours=hours_offset
    )
    return snapshot


def make_plugin_task_parameter_type(
    creator: models.User,
    group: models.Group,
    name: str = "test_param_type",
    description: str | None = None,
) -> models.PluginTaskParameterType:
    """Create a plugin task parameter type."""
    resource = models.Resource("plugin_task_parameter_type", group)
    return models.PluginTaskParameterType(
        name=name,
        description=description,
        structure=None,
        resource=resource,
        creator=creator,
    )


def make_artifact_with_task(
    creator: models.User,
    group: models.Group,
    job: models.Job,
    task: models.PluginTask,
    uri: str = "s3://test-bucket/test-artifact",
    is_dir: bool = False,
    file_size: int | None = None,
    description: str = "",
) -> models.Artifact:
    """Create an artifact linked to a plugin task."""
    artifact_resource = models.Resource("artifact", group)
    artifact = models.Artifact(
        uri=uri,
        is_dir=is_dir,
        file_size=file_size,
        description=description,
        resource=artifact_resource,
        creator=creator,
    )
    artifact.plugin_file_id = task.plugin_file_resource_snapshot_id
    artifact.task_name = task.plugin_task_name
    job.children.append(artifact_resource)
    return artifact


def make_artifact_task(
    plugin_file: models.PluginFile, task_name: str = "test_task"
) -> models.ArtifactTask:
    """Create a plugin task of type 'artifact'."""
    return models.ArtifactTask(
        plugin_task_name=task_name,
        file=plugin_file,
        output_parameters=[],
    )


def make_plugin_file(
    creator: models.User, group: models.Group, name: str = "test_plugin.py"
) -> models.PluginFile:
    """Create a plugin file."""
    resource = models.Resource("plugin_file", group)
    return models.PluginFile(
        filename=name,
        contents="# test plugin",
        description=None,
        resource=resource,
        creator=creator,
    )


def make_output_parameter(
    task: models.PluginTask,
    param_type: models.PluginTaskParameterType,
    parameter_number: int,
    value: str = "test",
) -> models.PluginTaskOutputParameter:
    """Create a plugin task output parameter."""
    output_param = models.PluginTaskOutputParameter(
        name=f"param_{parameter_number}",
        parameter_number=parameter_number,
        parameter_type=param_type,
    )
    task.output_parameters.append(output_param)
    return output_param


def _assert_snapshot_type(
    snapshot: models.ResourceSnapshot, snapshot_type: type[Any]
) -> Any:
    assert isinstance(snapshot, snapshot_type)
    return snapshot
