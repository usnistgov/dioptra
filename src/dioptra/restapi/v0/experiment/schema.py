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
"""The schemas for serializing/deserializing the experiment endpoint objects.

.. |Experiment| replace:: :py:class:`~.model.Experiment`
"""
from __future__ import annotations

from marshmallow import Schema, fields

from ...schemas import BasePageSchema


class ExperimentSchema(Schema):
    """The schema for the data stored in an |Experiment| object."""

    experimentId = fields.Integer(
        attribute="experiment_id",
        metadata=dict(description="An integer identifying a registered experiment."),
        dump_only=True,
    )
    createdOn = fields.DateTime(
        attribute="created_on",
        metadata=dict(description="The date and time the experiment was created."),
        dump_only=True,
    )
    lastModified = fields.DateTime(
        attribute="last_modified",
        metadata=dict(
            description="The date and time the experiment was last modified."
        ),
        dump_only=True,
    )
    name = fields.String(
        attribute="name", metadata=dict(description="The name of the experiment.")
    )


class IdStatusResponseSchema(Schema):
    """A simple response for reporting a status for one or more objects."""

    status = fields.String(
        attribute="status",
        metadata=dict(description="The status of the request."),
    )
    id = fields.List(
        fields.Integer(),
        attribute="id",
        metadata=dict(
            description="A list of integers identifying the affected object(s)."
        ),
    )


class NameStatusResponseSchema(Schema):
    """A simple response for reporting a status for one or more objects."""

    status = fields.String(
        attribute="status",
        metadata=dict(description="The status of the request."),
    )
    name = fields.List(
        fields.String(),
        attribute="name",
        metadata=dict(
            description="A list of names identifying the affected object(s)."
        ),
    )


class ExperimentPageResponseSchema(BasePageSchema):
    """A simple response for reporting a page of experiment objects."""

    data = fields.Nested(
        ExperimentSchema(many=True),
        attribute="data",
        metadata=dict(description="A list of experiment object data for the page."),
    )
