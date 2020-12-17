from typing import Any, Dict

from marshmallow import Schema, fields, post_dump, pre_dump

from .model import Queue, QueueLock, QueueRegistrationForm, QueueRegistrationFormData


class QueueLockSchema(Schema):
    __model__ = QueueLock

    queueId = fields.Integer(attribute="queue_id")
    createdOn = fields.DateTime(attribute="created_on")


class QueueSchema(Schema):
    __model__ = Queue

    queueId = fields.Integer(attribute="queue_id")
    createdOn = fields.DateTime(attribute="created_on")
    lastModified = fields.DateTime(attribute="last_modified")
    name = fields.String(attribute="name")


class QueueNameUpdateSchema(Schema):
    __model__ = Queue

    name = fields.String(attribute="name")


class QueueRegistrationFormSchema(Schema):
    __model__ = QueueRegistrationFormData

    name = fields.String(attribute="name", required=True)

    @pre_dump
    def extract_data_from_form(
        self, data: QueueRegistrationForm, many: bool, **kwargs
    ) -> Dict[str, Any]:
        def slugify(text: str) -> str:
            return text.lower().strip().replace(" ", "-")

        return {"name": slugify(data.name.data)}

    @post_dump
    def serialize_object(
        self, data: Dict[str, Any], many: bool, **kwargs
    ) -> QueueRegistrationFormData:
        return self.__model__(**data)  # type: ignore


QueueRegistrationSchema = [dict(name="name", type=str, location="form")]
