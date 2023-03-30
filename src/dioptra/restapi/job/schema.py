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
"""The schemas for serializing/deserializing the job endpoint objects.

.. |Job| replace:: :py:class:`~.model.Job`
.. |JobForm| replace:: :py:class:`~.model.JobForm`
.. |JobFormData| replace:: :py:class:`~.model.JobFormData`
"""
from __future__ import annotations

from typing import Any, Dict

from marshmallow import Schema, fields, post_dump, post_load, pre_dump, validate
from werkzeug.datastructures import FileStorage

from dioptra.restapi.utils import slugify

from .model import Job, JobForm, JobFormData


class JobSchema(Schema):
    """The schema for the data stored in a |Job| object.

    Attributes:
        jobId: A UUID that identifies the job.
        mlflowRunId: A UUID that identifies the MLFlow run associated with the job.
        experimentId: An integer identifying a registered experiment.
        queueId: An integer identifying a registered queue.
        createdOn: The date and time the job was created.
        lastModified: The date and time the job was last modified.
        timeout: The maximum alloted time for a job before it times out and is stopped.
        workflowUri: The URI pointing to the tarball archive or zip file uploaded with
            the job.
        entryPoint: The name of the entry point in the MLproject file to run.
        entryPointKwargs: A string listing parameter values to pass to the entry point
            for the job. The list of parameters is specified using the following format:
            `-P param1=value1 -P param2=value2`.
        dependsOn: A UUID for a previously submitted job to set as a dependency for the
            current job.
        status: The current status of the job. The allowed values are: `queued`,
            `started`, `deferred`, `finished`, `failed`.
    """

    __model__ = Job

    jobId = fields.String(
        attribute="job_id", metadata=dict(description="A UUID that identifies the job.")
    )
    mlflowRunId = fields.String(
        attribute="mlflow_run_id",
        allow_none=True,
        metadata=dict(
            description="A UUID that identifies the MLFLow run associated with the "
            "job.",
        ),
    )
    experimentId = fields.Integer(
        attribute="experiment_id",
        metadata=dict(description="An integer identifying a registered experiment."),
    )
    queueId = fields.Integer(
        attribute="queue_id",
        metadata=dict(description="An integer identifying a registered queue."),
    )
    createdOn = fields.DateTime(
        attribute="created_on",
        metadata=dict(description="The date and time the job was created."),
    )
    lastModified = fields.DateTime(
        attribute="last_modified",
        metadata=dict(description="The date and time the job was last modified."),
    )
    timeout = fields.String(
        attribute="timeout",
        allow_none=True,
        metadata=dict(
            description="The maximum alloted time for a job before it times out and "
            "is stopped.",
        ),
    )
    workflowUri = fields.String(
        attribute="workflow_uri",
        metadata=dict(
            description="The URI pointing to the tarball archive or zip file uploaded "
            "with the job.",
        ),
    )
    entryPoint = fields.String(
        attribute="entry_point",
        metadata=dict(
            description="The name of the entry point in the MLproject file to run.",
        ),
    )
    entryPointKwargs = fields.String(
        attribute="entry_point_kwargs",
        allow_none=True,
        metadata=dict(
            description="A string listing parameter values to pass to the entry point "
            "for the job. The list of parameters is specified using the following "
            'format: "-P param1=value1 -P param2=value2".',
        ),
    )
    dependsOn = fields.String(
        attribute="depends_on",
        allow_none=True,
        metadata=dict(
            description="A UUID for a previously submitted job to set as a dependency "
            "for the current job.",
        ),
    )
    status = fields.String(
        validate=validate.OneOf(
            ["queued", "started", "deferred", "finished", "failed"],
        ),
        metadata=dict(
            description="The current status of the job. The allowed values are: "
            "queued, started, deferred, finished, failed.",
        ),
    )

    @post_load
    def deserialize_object(self, data: Dict[str, Any], many: bool, **kwargs) -> Job:
        """Creates a |Job| object from the validated data."""
        return self.__model__(**data)


class JobFormSchema(Schema):
    """The schema for the information stored in a submitted job form.

    Attributes:
        experiment_name: The name of a registered experiment.
        queue: The name of an active queue.
        timeout: The maximum alloted time for a job before it times out and is stopped.
            If omitted, the job timeout will default to 24 hours.
        entry_point: The name of the entry point in the MLproject file to run.
        entry_point_kwargs: A list of entry point parameter values to use for the job.
            The list is a string with the following format: `-P param1=value1
            -P param2=value2`. If omitted, the default values in the MLproject file will
            be used.
        depends_on: A job UUID to set as a dependency for this new job. The new job will
            not run until this job completes successfully. If omitted, then the new job
            will start as soon as computing resources are available.
        workflow: A tarball archive or zip file containing, at a minimum, a MLproject
            file and its associated entry point scripts.
    """

    __model__ = JobFormData

    experiment_name = fields.String(
        required=True, metadata=dict(description="The name of a registered experiment.")
    )
    queue = fields.String(
        required=True, metadata=dict(description="The name of an active queue")
    )
    timeout = fields.String(
        allow_none=True,
        metadata=dict(
            description="The maximum alloted time for a job before it times out and "
            "is stopped. If omitted, the job timeout will default to 24 hours.",
        ),
    )
    entry_point = fields.String(
        required=True,
        metadata=dict(
            description="The name of the entry point in the MLproject file to run.",
        ),
    )
    entry_point_kwargs = fields.String(
        allow_none=True,
        metadata=dict(
            description="A list of entry point parameter values to use for the job. "
            'The list is a string with the following format: "-P param1=value1 '
            '-P param2=value2". If omitted, the default values in the MLproject '
            "file will be used.",
        ),
    )
    depends_on = fields.String(
        allow_none=True,
        metadata=dict(
            description="A job UUID to set as a dependency for this new job. The new "
            "job will not run until this job completes successfully. If omitted, then "
            "the new job will start as soon as computing resources are available.",
        ),
    )
    workflow = fields.Raw(
        metadata=dict(
            description="A tarball archive or zip file containing, at a minimum, a "
            "MLproject file and its associated entry point scripts.",
        ),
    )

    @pre_dump
    def extract_data_from_form(
        self, data: JobForm, many: bool, **kwargs
    ) -> Dict[str, Any]:
        """Extracts data from the |JobForm| for validation."""

        return {
            "experiment_name": slugify(data.experiment_name.data),
            "queue": slugify(data.queue.data),
            "timeout": data.timeout.data or None,
            "entry_point": data.entry_point.data,
            "entry_point_kwargs": data.entry_point_kwargs.data or None,
            "depends_on": data.depends_on.data or None,
            "workflow": data.workflow.data,
        }

    @post_dump
    def serialize_object(
        self, data: Dict[str, Any], many: bool, **kwargs
    ) -> JobFormData:
        """Creates a |JobFormData| object from the validated data."""
        return self.__model__(**data)


job_submit_form_schema = [
    dict(
        name="experiment_name",
        type=str,
        location="form",
        required=True,
        help="The name of a registered experiment.",
    ),
    dict(
        name="queue",
        type=str,
        location="form",
        required=True,
        help="The name of an active queue.",
    ),
    dict(
        name="timeout",
        type=str,
        location="form",
        required=False,
        help="The maximum alloted time for a job before it times out and is stopped. "
        "If omitted, the job timeout will default to 24 hours.",
    ),
    dict(
        name="entry_point",
        type=str,
        location="form",
        required=True,
        help="The name of the entry point in the MLproject file to run.",
    ),
    dict(
        name="entry_point_kwargs",
        type=str,
        location="form",
        required=False,
        help="A list of entry point parameter values to use for the job. The list is "
        'a string with the following format: "-P param1=value1 -P param2=value2". '
        "If omitted, the default values in the MLproject file will be used.",
    ),
    dict(
        name="depends_on",
        type=str,
        location="form",
        required=False,
        help="A job UUID to set as a dependency for this new job. The new job will "
        "not run until this job completes successfully. If omitted, then the new job"
        "will start as soon as computing resources are available.",
    ),
    dict(
        name="workflow",
        type=FileStorage,
        location="files",
        required=True,
        help="A tarball archive or zip file containing, at a minimum, a MLproject file "
        "and its associated entry point scripts.",
    ),
]
