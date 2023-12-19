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
"""
from __future__ import annotations

from marshmallow import Schema, fields, validate

from dioptra.restapi.custom_schema_fields import FileUpload


class JobSchema(Schema):
    """The schema for the data stored in a |Job| object."""

    jobId = fields.String(
        attribute="job_id",
        metadata=dict(description="A UUID that identifies the job."),
        dump_only=True,
    )
    mlflowRunId = fields.String(
        attribute="mlflow_run_id",
        allow_none=True,
        metadata=dict(
            description="A UUID that identifies the MLFLow run associated with the "
            "job.",
        ),
        dump_only=True,
    )
    experimentId = fields.Integer(
        attribute="experiment_id",
        metadata=dict(description="An integer identifying a registered experiment."),
        dump_only=True,
    )
    experimentName = fields.String(
        attribute="experiment_name",
        metadata=dict(description="The name of a registered experiment."),
        load_only=True,
    )
    queueId = fields.Integer(
        attribute="queue_id",
        metadata=dict(description="An integer identifying a registered queue."),
        dump_only=True,
    )
    queue = fields.String(
        metadata=dict(description="The name of an active queue"),
        load_only=True,
    )
    createdOn = fields.DateTime(
        attribute="created_on",
        metadata=dict(description="The date and time the job was created."),
        dump_only=True,
    )
    lastModified = fields.DateTime(
        attribute="last_modified",
        metadata=dict(description="The date and time the job was last modified."),
        dump_only=True,
    )
    timeout = fields.String(
        attribute="timeout",
        load_default="24h",
        metadata=dict(
            description="The maximum alloted time for a job before it times out and "
            "is stopped. If omitted, the job timeout will default to 24 hours.",
        ),
    )
    workflow = FileUpload(
        metadata=dict(
            description="A tarball archive or zip file containing, at a minimum, a "
            "MLproject file and its associated entry point scripts.",
        ),
        load_only=True,
    )
    workflowUri = fields.String(
        attribute="workflow_uri",
        metadata=dict(
            description="The URI pointing to the tarball archive or zip file uploaded "
            "with the job.",
        ),
        dump_only=True,
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
        load_default=None,
        metadata=dict(
            description="A string listing parameter values to pass to the entry point "
            "for the job. The list of parameters is specified using the following "
            'format: "-P param1=value1 -P param2=value2".',
        ),
    )
    dependsOn = fields.String(
        attribute="depends_on",
        allow_none=True,
        load_default=None,
        metadata=dict(
            description="A job UUID to set as a dependency for this new job. The new "
            "job will not run until this job completes successfully. If omitted, then "
            "the new job will start as soon as computing resources are available.",
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
        #dump_only=True,
    )


class TaskEngineSubmission(Schema):
    queue = fields.String(
        required=True,
        metadata={"description": "The name of an active queue"},
    )

    experimentName = fields.String(
        required=True,
        metadata={"description": "The name of a registered experiment."},
    )

    experimentDescription = fields.Dict(
        keys=fields.String(),
        required=True,
        metadata={"description": "A declarative experiment description."},
    )

    globalParameters = fields.Dict(
        keys=fields.String(),
        metadata={"description": "Global parameters for this task engine job."},
    )

    timeout = fields.String(
        metadata={
            "description": "The maximum alloted time for a job before it times"
            " out and is stopped. If omitted, the job timeout"
            " will default to 24 hours.",
        },
    )

    dependsOn = fields.String(
        metadata={
            "description": "A job UUID to set as a dependency for this new job."
            " The new job will not run until this job completes"
            " successfully. If omitted, then the new job will"
            " start as soon as computing resources are"
            " available.",
        },
    )
