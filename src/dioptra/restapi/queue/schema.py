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
"""The schemas for serializing/deserializing the queue endpoint objects.

.. |Queue| replace:: :py:class:`~.model.Queue`
.. |QueueLock| replace:: :py:class:`~.model.QueueLock`
.. |QueueRegistrationForm| replace:: :py:class:`~.model.QueueRegistrationForm`
.. |QueueRegistrationFormData| replace:: :py:class:`~.model.QueueRegistrationFormData`
"""
from __future__ import annotations

from typing import Any, Dict

from marshmallow import Schema, fields, post_dump, pre_dump

from dioptra.restapi.utils import slugify

from .model import Queue, QueueLock, QueueRegistrationForm, QueueRegistrationFormData


class QueueLockSchema(Schema):
    """The schema for the data stored in a |QueueLock| object.

    Attributes:
        queueId: An integer identifying a registered queue.
        createdOn: The date and time the queue lock was created.
    """

    __model__ = QueueLock

    queueId = fields.Integer(
        attribute="queue_id",
        metadata=dict(description="An integer identifying a registered queue."),
    )
    createdOn = fields.DateTime(
        attribute="created_on",
        metadata=dict(description="The date and time the queue lock was created."),
    )


class QueueSchema(Schema):
    """The schema for the data stored in a |Queue| object.

    Attributes:
        queueId: An integer identifying a registered queue.
        createdOn: The date and time the queue was created.
        lastModified: The date and time the queue was last modified.
        name: The name of the queue.
    """

    __model__ = Queue

    queueId = fields.Integer(
        attribute="queue_id",
        metadata=dict(description="An integer identifying a registered queue."),
    )
    createdOn = fields.DateTime(
        attribute="created_on",
        metadata=dict(description="The date and time the queue was created."),
    )
    lastModified = fields.DateTime(
        attribute="last_modified",
        metadata=dict(description="The date and time the queue was last modified."),
    )
    name = fields.String(
        attribute="name", metadata=dict(description="The name of the queue.")
    )


class QueueNameUpdateSchema(Schema):
    """The schema for the data used to update a |Queue| object.

    Attributes:
        name: The new name for the queue. Must be unique.
    """

    __model__ = Queue

    name = fields.String(
        attribute="name",
        metadata=dict(description="The new name for the queue. Must be unique."),
    )


class QueueRegistrationFormSchema(Schema):
    """The schema for the information stored in a queue registration form.

    Attributes:
        name: The name of the queue. Must be unique.
    """

    __model__ = QueueRegistrationFormData

    name = fields.String(
        attribute="name",
        required=True,
        metadata=dict(description="The name of the queue. Must be unique."),
    )

    @pre_dump
    def extract_data_from_form(
        self, data: QueueRegistrationForm, many: bool, **kwargs
    ) -> Dict[str, Any]:
        """Extracts data from the |QueueRegistrationForm| for validation."""

        return {"name": slugify(data.name.data)}

    @post_dump
    def serialize_object(
        self, data: Dict[str, Any], many: bool, **kwargs
    ) -> QueueRegistrationFormData:
        """Creates a |QueueRegistrationFormData| object from the validated data."""
        return self.__model__(**data)


QueueRegistrationSchema = [
    dict(
        name="name",
        type=str,
        location="form",
        required=True,
        help="The name of the queue. Must be unique.",
    )
]
