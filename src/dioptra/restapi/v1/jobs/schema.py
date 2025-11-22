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
"""The schemas for serializing/deserializing Job resources."""

import enum
import re

import nh3
from marshmallow import Schema, fields, post_load, validate

from dioptra.restapi.v1.artifacts.schema import ArtifactRefSchema
from dioptra.restapi.v1.schemas import (
    BasePageSchema,
    GroupIdQueryParametersSchema,
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
    SortByGetQueryParametersSchema,
    generate_base_resource_ref_schema,
    generate_base_resource_schema,
)

ALLOWED_METRIC_NAME_REGEX = re.compile(r"^([A-Z]|[A-Z_][A-Z0-9_]+)$", flags=re.IGNORECASE)  # fmt: skip


JobRefSchema = generate_base_resource_ref_schema("Job")
JobSnapshotRefSchema = generate_base_resource_ref_schema("Job", keep_snapshot_id=True)


class JobMlflowRunSchema(Schema):
    """The schema for the data in a mlflowRun resource."""

    mlflowRunId = fields.UUID(
        attribute="mlflow_run_id",
        metadata={"description": "UUID for the associated Mlflow Run."},
    )


class JobIdSchema(Schema):
    id = fields.Integer(
        attribute="id",
        metadata={"description": "ID for the Job resource."},
        dump_only=True,
    )


class MetricsSchema(Schema):
    name = fields.String(
        attribute="name",
        metadata={"description": "The name of the metric."},
        required=True,
        validate=validate.Regexp(
            ALLOWED_METRIC_NAME_REGEX,
            error=(
                "'{input}' is not a compatible name for a metric. "
                "A metric name must start with a letter or underscore, "
                "followed by letters, numbers, or underscores. In "
                "addition, '_' is not a valid metric name."
            ),
        ),
    )

    value = fields.Float(
        attribute="value",
        allow_none=True,
        metadata={"description": "The value of the metric."},
        required=True,
    )

    step = fields.Integer(
        attribute="step",
        metadata={"description": "The step value for the metric."},
        load_only=True,
        required=False,
        load_default=0,
    )


class MetricsSnapshotSchema(Schema):
    name = fields.String(
        attribute="name",
        metadata={"description": "The name of the metric."},
    )
    value = fields.Float(
        attribute="value",
        metadata={"description": "The value of the metric."},
    )
    step = fields.Integer(
        attribute="step",
        metadata={"description": "The step value for the metric."},
    )
    timestamp = fields.Integer(
        attribute="timestamp",
        metadata={"description": "The timestamp of the metric in milliseconds."},
    )


class MetricsSnapshotPageSchema(BasePageSchema):
    data = fields.Nested(
        MetricsSnapshotSchema,
        many=True,
        metadata={"description": "List of Metric Snapshots in the current page."},
    )


class JobIdMetricsSchema(JobIdSchema):
    metrics = fields.Nested(
        MetricsSchema,
        attribute="metrics",
        metadata={
            "description": "A list of the latest metrics associated with the job."
        },
        many=True,
    )


class ExperimentJobsMetricsSchema(BasePageSchema):
    data = fields.Nested(
        JobIdMetricsSchema,
        many=True,
        metadata={"description": "List of metrics for each job in the experiment"},
    )


class JobStatusSchema(JobIdSchema):
    """The fields schema for the data in a Job status resource."""

    status = fields.String(
        attribute="status",
        validate=validate.OneOf(
            ["queued", "started", "deferred", "finished", "failed", "reset"],
        ),
        metadata={
            "description": "The current status of the job. The allowed values are: "
            "queued, started, deferred, finished, failed, reset.",
        },
    )


JobBaseSchema = generate_base_resource_schema("Job", snapshot=True)


class JobArtifactValueSchema(Schema):
    id = fields.Int(
        attribute="id",
        metadata={"description": "Artifact Resoure Id."},
    )
    snapshotId = fields.Int(
        attribute="snapshot_id",
        metadata={"description": "Artifact Resoure Snapshot Id."},
    )


class JobSchema(JobBaseSchema):  # type: ignore
    """The schema for the data stored in a Job resource."""

    from dioptra.restapi.v1.entrypoints.schema import EntrypointSnapshotRefSchema
    from dioptra.restapi.v1.experiments.schema import ExperimentSnapshotRefSchema
    from dioptra.restapi.v1.queues.schema import QueueSnapshotRefSchema

    description = fields.String(
        attribute="description",
        metadata={"description": "Description of the Job resource."},
        load_default=None,
    )
    queueId = fields.Integer(
        attribute="queue_id",
        data_key="queue",
        metadata={"description": "An integer identifying a registered queue."},
        load_only=True,
        required=True,
    )
    queue = fields.Nested(
        QueueSnapshotRefSchema,
        attribute="queue",
        metadata={"description": "The active queue used to run the Job."},
        dump_only=True,
    )
    experiment = fields.Nested(
        ExperimentSnapshotRefSchema,
        attribute="experiment",
        metadata={"description": "The registered experiment associated with the Job."},
        dump_only=True,
    )
    entrypointId = fields.Integer(
        attribute="entrypoint_id",
        data_key="entrypoint",
        metadata={"description": "An integer identifying a registered entry point."},
        load_only=True,
        required=True,
    )
    entrypoint = fields.Nested(
        EntrypointSnapshotRefSchema,
        attribute="entrypoint",
        metadata={"description": "The entry point associated with the Job."},
        dump_only=True,
    )
    values = fields.Dict(
        keys=fields.String(),
        values=fields.String(),
        attribute="values",
        allow_none=True,
        metadata={
            "description": (
                "A dictionary of keyword arguments to pass to the Job's Entrypoint."
            ),
        },
        load_default=dict,
    )
    artifactValues = fields.Dict(
        keys=fields.String(),
        values=fields.Nested(JobArtifactValueSchema),
        attribute="artifact_values",
        allow_none=True,
        metadata={
            "description": (
                "A dictionary of artifacts to pass to the Job's Entrypoint."
            ),
        },
    )
    timeout = fields.String(
        attribute="timeout",
        load_default="24h",
        metadata={
            "description": "The maximum alloted time for a job before it times out and "
            "is stopped. If omitted, the job timeout will default to 24 hours.",
        },
    )
    status = fields.String(
        attribute="status",
        metadata={
            "description": "The current status of the job. The allowed values are: "
            "queued, started, deferred, finished, failed.",
        },
        dump_only=True,
    )
    artifacts = fields.Nested(
        ArtifactRefSchema,
        attribute="artifacts",
        many=True,
        metadata={"description": "Artifacts created by the Job resource."},
        dump_only=True,
    )


class JobCreateRequestSchema(JobSchema):
    """The schema for creating a Job resource."""

    entrypointSnapshotId = fields.Integer(
        attribute="entrypoint_snapshot_id",
        data_key="entrypointSnapshot",
        allow_none=True,
        metadata={
            "description": (
                "An integer identifying a snapshot ID associated with the entrypoint. "
                "If specified, the snapshotted version of the entrypoint will be used "
                "to run the job. If not specified, the job will default to using the "
                "latest version of the entrypoint."
            )
        },
        required=False,
        load_default=None,
    )


class JobPageSchema(BasePageSchema):
    """The paged schema for the data stored in a Job resource."""

    data = fields.Nested(
        JobSchema,
        many=True,
        metadata={"description": "List of Job resources in the current page."},
    )


class MetricsSnapshotsGetQueryParameters(
    PagingQueryParametersSchema,
):
    """The query parameters for the GET method of the
    /jobs/{id}/metrics/{name}/snapshots endpoint."""


class JobGetQueryParameters(
    PagingQueryParametersSchema,
    GroupIdQueryParametersSchema,
    SearchQueryParametersSchema,
    SortByGetQueryParametersSchema,
):
    """The query parameters for the GET method of the /jobs endpoint."""


class ExperimentJobGetQueryParameters(
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
    SortByGetQueryParametersSchema,
):
    """The query parameters for the GET method of the /experiments/{id}/jobs
    endpoint."""


class JobLogSeverity(enum.Enum):
    DEBUG = enum.auto()
    INFO = enum.auto()
    WARNING = enum.auto()
    ERROR = enum.auto()
    CRITICAL = enum.auto()


class JobLogRecordSchema(Schema):
    """
    A logging record within the context of a running job.
    """

    severity = fields.Enum(
        JobLogSeverity,
        attribute="severity",
        metadata={
            "description": "Log severity level: {}".format(
                ", ".join(e.name for e in JobLogSeverity)
            )
        },
        required=True,
    )
    loggerName = fields.String(
        attribute="logger_name",
        metadata={
            "description": "The name of the logger that emitted the log message."
        },
        required=True,
    )
    message = fields.String(
        attribute="message",
        metadata={"description": "The logged message."},
        required=True,
    )
    createdOn = fields.DateTime(
        attribute="created_on",
        metadata={"description": "Server timestamp for when the job log was received."},
        dump_only=True,
    )

    @post_load
    def sanitize_logger_name(self, in_data, **kwargs):
        in_data["logger_name"] = nh3.clean(in_data["logger_name"])
        return in_data

    @post_load
    def sanitize_message(self, in_data, **kwargs):
        in_data["message"] = nh3.clean(in_data["message"])
        return in_data


class JobLogRecordsSchema(Schema):
    """
    A list of logging records. Used for upload.
    """

    data = fields.Nested(
        JobLogRecordSchema,
        many=True,
        validate=validate.Length(min=1),
        required=True,
    )


class JobLogRecordsPageSchema(BasePageSchema):
    """
    A page of logging records with detailed paging information. Used for download.
    """

    data = fields.Nested(
        JobLogRecordSchema,
        many=True,
        validate=validate.Length(min=1),
        required=True,
    )


class JobLogGetQueryParameters(PagingQueryParametersSchema):
    """
    The query parameters for the GET method of the /jobs/{id}/log endpoint.
    """
