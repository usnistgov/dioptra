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
from marshmallow import Schema, fields, validate

from dioptra.restapi.v1.schemas import (
    BasePageSchema,
    GroupIdQueryParametersSchema,
    PagingQueryParametersSchema,
    SearchQueryParametersSchema,
    generate_base_resource_ref_schema,
    generate_base_resource_schema,
)

JobRefSchema = generate_base_resource_ref_schema("Job")


class JobStatusSchema(Schema):
    """The fields schema for the data in a Job status resource."""

    status = fields.String(
        validate=validate.OneOf(
            ["queued", "started", "deferred", "finished", "failed"],
        ),
        metadata=dict(
            description="The current status of the job. The allowed values are: "
            "queued, started, deferred, finished, failed.",
        ),
        dump_only=True,
    )


JobBaseSchema = generate_base_resource_schema("Job", snapshot=True)


class JobSchema(JobStatusSchema, JobBaseSchema):  # type: ignore
    """The schema for the data stored in a Job resource."""

    from dioptra.restapi.v1.entrypoints.schema import EntrypointRefSchema
    from dioptra.restapi.v1.experiments.schema import ExperimentRefSchema
    from dioptra.restapi.v1.queues.schema import QueueRefSchema

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
        QueueRefSchema,
        attribute="queue",
        metadata=dict(description="The active queue used to run the Job."),
        dump_only=True,
    )
    experimentId = fields.Integer(
        attribute="experiment_id",
        data_key="experiment",
        metadata=dict(description="An integer identifying a registered experiment."),
        load_only=True,
        required=True,
    )
    experiment = fields.Nested(
        ExperimentRefSchema,
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
        EntrypointRefSchema,
        attribute="entrypoint",
        metadata=dict(description="The entry point associated with the Job."),
        dump_only=True,
    )
    values = fields.List(
        fields.String(),
        attribute="values",
        allow_none=True,
        load_default=None,
        metadata=dict(
            description="A list of parameter values to pass to the Job's Entrypoint.",
        ),
    )
    timeout = fields.String(
        attribute="timeout",
        load_default="24h",
        metadata=dict(
            description="The maximum alloted time for a job before it times out and "
            "is stopped. If omitted, the job timeout will default to 24 hours.",
        ),
        dump_only=True,
    )


class JobPageSchema(BasePageSchema):
    """The paged schema for the data stored in a Job resource."""

    data = fields.Nested(
        JobSchema,
        many=True,
        metadata=dict(description="List of Job resources in the current page."),
    )


class JobGetQueryParameters(
    PagingQueryParametersSchema,
    GroupIdQueryParametersSchema,
    SearchQueryParametersSchema,
):
    """The query parameters for the GET method of the /jobs endpoint."""
