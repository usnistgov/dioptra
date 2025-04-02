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
import math
import re

from marshmallow import Schema, fields, validate, post_dump

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

ALLOWED_METRIC_NAME_REGEX = re.compile(r"^([A-Z]|[A-Z_][A-Z0-9_]+)$", flags=re.IGNORECASE)  # noqa: B950; fmt: skip


JobRefSchema = generate_base_resource_ref_schema("Job")
JobSnapshotRefSchema = generate_base_resource_ref_schema("Job", keep_snapshot_id=True)


class JobMlflowRunSchema(Schema):
    """The schema for the data in a mlflowRun resource."""

    mlflowRunId = fields.UUID(
        attribute="mlflow_run_id",
        metadata=dict(description="UUID for the associated Mlflow Run."),
    )


class JobIdSchema(Schema):
    id = fields.Integer(
        attribute="id",
        metadata=dict(description="ID for the Job resource."),
        dump_only=True,
    )


class MetricsSchema(Schema):
    name = fields.String(
        attribute="name",
        metadata=dict(description="The name of the metric."),
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
        allow_nan=True,
        metadata=dict(description="The value of the metric."),
        required=True,
    )

    step = fields.Integer(
        attribute="step",
        metadata=dict(description="The step value for the metric."),
        load_only=True,
        required=False,
        load_default=0,
    )

    @post_dump
    def convert_nan(self, item, many, **kwargs):
        if math.isnan(item["value"]):
            item["value"] = "nan"
        return item


class MetricsSnapshotSchema(Schema):
    name = fields.String(
        attribute="name",
        metadata=dict(description="The name of the metric."),
    )
    value = fields.Float(
        attribute="value",
        metadata=dict(description="The value of the metric."),
    )
    step = fields.Integer(
        attribute="step",
        metadata=dict(description="The step value for the metric."),
    )
    timestamp = fields.Integer(
        attribute="timestamp",
        metadata=dict(description="The timestamp of the metric in milliseconds."),
    )


class MetricsSnapshotPageSchema(BasePageSchema):
    data = fields.Nested(
        MetricsSnapshotSchema,
        many=True,
        metadata=dict(description="List of Metric Snapshots in the current page."),
    )


class JobIdMetricsSchema(JobIdSchema):
    metrics = fields.Nested(
        MetricsSchema,
        attribute="metrics",
        metadata=dict(
            description="A list of the latest metrics associated with the job."
        ),
        many=True,
    )


class ExperimentJobsMetricsSchema(BasePageSchema):
    data = fields.Nested(
        JobIdMetricsSchema,
        many=True,
        metadata=dict(description="List of metrics for each job in the experiment"),
    )


class JobStatusSchema(JobIdSchema):
    """The fields schema for the data in a Job status resource."""

    status = fields.String(
        attribute="status",
        validate=validate.OneOf(
            ["queued", "started", "deferred", "finished", "failed"],
        ),
        metadata=dict(
            description="The current status of the job. The allowed values are: "
            "queued, started, deferred, finished, failed.",
        ),
    )


JobBaseSchema = generate_base_resource_schema("Job", snapshot=True)


class JobSchema(JobBaseSchema):  # type: ignore
    """The schema for the data stored in a Job resource."""

    from dioptra.restapi.v1.entrypoints.schema import EntrypointSnapshotRefSchema
    from dioptra.restapi.v1.experiments.schema import ExperimentSnapshotRefSchema
    from dioptra.restapi.v1.queues.schema import QueueSnapshotRefSchema

    description = fields.String(
        attribute="description",
        metadata=dict(description="Description of the Job resource."),
        load_default=None,
    )
    queueId = fields.Integer(
        attribute="queue_id",
        data_key="queue",
        metadata=dict(description="An integer identifying a registered queue."),
        load_only=True,
        required=True,
    )
    queue = fields.Nested(
        QueueSnapshotRefSchema,
        attribute="queue",
        metadata=dict(description="The active queue used to run the Job."),
        dump_only=True,
    )
    experiment = fields.Nested(
        ExperimentSnapshotRefSchema,
        attribute="experiment",
        metadata=dict(description="The registered experiment associated with the Job."),
        dump_only=True,
    )
    entrypointId = fields.Integer(
        attribute="entrypoint_id",
        data_key="entrypoint",
        metadata=dict(description="An integer identifying a registered entry point."),
        load_only=True,
        required=True,
    )
    entrypoint = fields.Nested(
        EntrypointSnapshotRefSchema,
        attribute="entrypoint",
        metadata=dict(description="The entry point associated with the Job."),
        dump_only=True,
    )
    values = fields.Dict(
        keys=fields.String(),
        values=fields.String(),
        attribute="values",
        allow_none=True,
        metadata=dict(
            description=(
                "A dictionary of keyword arguments to pass to the Job's Entrypoint."
            ),
        ),
    )
    timeout = fields.String(
        attribute="timeout",
        load_default="24h",
        metadata=dict(
            description="The maximum alloted time for a job before it times out and "
            "is stopped. If omitted, the job timeout will default to 24 hours.",
        ),
    )
    status = fields.String(
        attribute="status",
        metadata=dict(
            description="The current status of the job. The allowed values are: "
            "queued, started, deferred, finished, failed.",
        ),
        dump_only=True,
    )
    artifacts = fields.Nested(
        ArtifactRefSchema,
        attribute="artifacts",
        many=True,
        metadata=dict(description="Artifacts created by the Job resource."),
        dump_only=True,
    )


class JobPageSchema(BasePageSchema):
    """The paged schema for the data stored in a Job resource."""

    data = fields.Nested(
        JobSchema,
        many=True,
        metadata=dict(description="List of Job resources in the current page."),
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
