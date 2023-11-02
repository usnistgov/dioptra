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

from dioptra.restapi.utils import ParametersSchema, slugify

from .model import Group, GroupForm, GroupFormData


class GroupSchema(Schema):
    """The schema for the data stored in a |Group| object.

    Attributes:
        group_id: The unique identifier of the group.
        name: Human-readable name for the group.
        creator_id: The id for the user that created the group.
        owner_id: The id for the user that owns the group.
        created_on: The time at which the group was created.
        deleted: Whether the group has been deleted.
    """

    __model__ = Group

    group_id = fields.Integer(
        attribute="id", metadata=dict(description="A UUID that identifies the group.")
    )
    name = fields.String(
        attribute="name",
        allow_none=True, #should we force the user to pick a name?
        metadata=dict(
            description="Human-readable name for the group.",
        ),
    )
    creator_id = fields.Integer(
        attribute="creator_id",
        metadata=dict(description="An integer identifying"
                      "the user that created the group."),
    )
    owner_id = fields.Integer(
        attribute="owner_id",
        metadata=dict(description="An integer identifying the user that owns"
                       "the group."),
    )
    createdOn = fields.DateTime(
        attribute="created_on",
        metadata=dict(description="The date and time the group was created."),
    )
    deleted = fields.Boolean(
        attribute="deleted",
        metadata=dict(description="Whether the group has been deleted.")
    )

    @post_load
    def deserialize_object(self, data: Dict[str, Any], many: bool, **kwargs) -> Group:
        """Creates a |Job| object from the validated data."""
        return self.__model__(**data)


# class GroupFormSchema(Schema):
#     """The schema for the information stored in a submitted group form.

#     Attributes:
#         group_name: The name of a registered experiment.
#     """

#     __model__ = GroupFormData

#     group_name = fields.String(
#         required=True, metadata=dict(description="The name of the group being "
#                                      "registered.")
#     )
    
#     @pre_dump
#     def extract_data_from_form(
#         self, data: GroupForm, many: bool, **kwargs
#     ) -> Dict[str, Any]:
#         """Extracts data from the |GroupForm| for validation."""

#         return {
#             "group_name": slugify(data.group_name.data),
#         }

#     @post_dump
#     def serialize_object(
#         self, data: Dict[str, Any], many: bool, **kwargs
#     ) -> GroupFormData:
#         """Creates a |GroupFormData| object from the validated data."""
#         return self.__model__(**data)


# group_submit_form_schema: list[ParametersSchema] = [
#     dict(
#         name="group_name",
#         type=str,
#         location="form",
#         required=True,
#         help="The name of the group being registered.",
#     ),
# ]
