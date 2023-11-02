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

from .model import GroupMembership


class GroupMembershipSchema(Schema):
    """The schema for the data stored in a GroupMembership object.

    Attributes:
        user_id: The ID of the user who is a member of the group.
        group_id: The ID of the group to which the user belongs.
        read: Indicates whether the user has read permissions in the group.
        write: Indicates whether the user has write permissions in the group.
        share_read: Indicates whether the user can share read permissions with others in the group.
        share_write: Indicates whether the user can share write permissions with others in the group.
    """

    __model__ = GroupMembership

    user_id = fields.Integer(
        attribute="user_id",
        metadata=dict(description="The ID of the user who is a member of the group."),
    )
    group_id = fields.String(
        attribute="group_id",
        metadata=dict(description="The ID of the group to which the user belongs."),
    )
    read = fields.Boolean(
        attribute="read",
        metadata=dict(description="Indicates whether the user has read permissions in the group."),
    )
    write = fields.Boolean(
        attribute="write",
        metadata=dict(description="Indicates whether the user has write permissions in the group."),
    )
    share_read = fields.Boolean(
        attribute="share_read",
        metadata=dict(description="Indicates whether the user can share read permissions with others in the group."),
    )
    share_write = fields.Boolean(
        attribute="share_write",
        metadata=dict(description="Indicates whether the user can share write permissions with others in the group."),
    )

    @post_load
    def deserialize_object(self, data: Dict[str, Any], many: bool, **kwargs) -> GroupMembership:
        """Creates a GroupMembership object from the validated data."""
        return self.__model__(**data)


# class GroupMembershipFormSchema(Schema):
#     """The schema for the information stored in a submitted group membership form.

#     Attributes:
#         group_id: The ID of the group to which the user belongs.
#         user_id: The ID of the user to add to the group.
#         read: Indicates whether read permission is granted.
#         write: Indicates whether write permission is granted.
#         share_read: Indicates whether share read permission is granted.
#         share_write: Indicates whether share write permission is granted.
#     """

#     __model__ = GroupMembershipFormData

#     group_id = fields.String(
#         attribute="group_id",
#         metadata=dict(description="The ID of the group to which the user belongs."),
#     )
#     user_id = fields.Integer(
#         required=True,
#         metadata=dict(description="The ID of the user to add to the group.")
#     )
#     read = fields.Boolean(
#         metadata=dict(description="Indicates whether read permission is granted.")
#     )
#     write = fields.Boolean(
#         metadata=dict(description="Indicates whether write permission is granted.")
#     )
#     share_read = fields.Boolean(
#         metadata=dict(description="Indicates whether share read permission is granted.")
#     )
#     share_write = fields.Boolean(
#         metadata=dict(description=
#                       "Indicates whether share write permission is granted.")
#     )

#     @pre_dump
#     def extract_data_from_form(
#         self, data: GroupMembershipForm, many: bool, **kwargs
#     ) -> Dict[str, Any]:
#         """Extracts data from the GroupMembershipForm for validation."""
#         return {
#             "group_id": data.group_id.data,
#             "user_id": data.user_id.data,
#             "read": data.read.data,
#             "write": data.write.data,
#             "share_read": data.share_read.data,
#             "share_write": data.share_write.data,
#         }

#     @post_dump
#     def serialize_object(
#         self, data: Dict[str, Any], many: bool, **kwargs
#     ) -> GroupMembershipFormData:
#         """Creates a GroupMembershipFormData object from the validated data."""
#         return self.__model__(**data)


# group_membership_form_schema: list[ParametersSchema] = [
#     {
#         "name": "group_id",
#         "type": int,
#         "location": "form",
#         "required": True,
#         "help": "The ID of the group to add the user to."
#     },
#     {
#         "name": "user_id",
#         "type": int,
#         "location": "form",
#         "required": True,
#         "help": "The ID of the user to add to the group."
#     },
#     {
#         "name": "read",
#         "type": bool,
#         "location": "form",
#         "required": False,
#         "help": "Indicates whether read permission is granted."
#     },
#     {
#         "name": "write",
#         "type": bool,
#         "location": "form",
#         "required": False,
#         "help": "Indicates whether write permission is granted."
#     },
#     {
#         "name": "share_read",
#         "type": bool,
#         "location": "form",
#         "required": False,
#         "help": "Indicates whether share read permission is granted."
#     },
#     {
#         "name": "share_write",
#         "type": bool,
#         "location": "form",
#         "required": False,
#         "help": "Indicates whether share write permission is granted."
#     }
# ]
