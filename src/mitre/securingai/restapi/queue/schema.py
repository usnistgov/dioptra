"""The schemas for serializing/deserializing the queue endpoint objects.

.. |Queue| replace:: :py:class:`~.model.Queue`
.. |QueueLock| replace:: :py:class:`~.model.QueueLock`
.. |QueueRegistrationForm| replace:: :py:class:`~.model.QueueRegistrationForm`
.. |QueueRegistrationFormData| replace:: :py:class:`~.model.QueueRegistrationFormData`
"""

from typing import Any, Dict

from marshmallow import Schema, fields, post_dump, pre_dump

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

        def slugify(text: str) -> str:
            return text.lower().strip().replace(" ", "-")

        return {"name": slugify(data.name.data)}

    @post_dump
    def serialize_object(
        self, data: Dict[str, Any], many: bool, **kwargs
    ) -> QueueRegistrationFormData:
        """Creates a |QueueRegistrationFormData| object from the validated data."""
        return self.__model__(**data)  # type: ignore


QueueRegistrationSchema = [
    dict(
        name="name",
        type=str,
        location="form",
        required=True,
        help="The name of the queue. Must be unique.",
    )
]
