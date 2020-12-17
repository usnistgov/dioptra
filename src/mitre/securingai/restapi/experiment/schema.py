from typing import Any, Dict

from marshmallow import Schema, fields, post_dump, pre_dump

from .model import (
    Experiment,
    ExperimentRegistrationForm,
    ExperimentRegistrationFormData,
)


class ExperimentSchema(Schema):
    __model__ = Experiment

    experimentId = fields.Integer(attribute="experiment_id")
    createdOn = fields.DateTime(attribute="created_on")
    lastModified = fields.DateTime(attribute="last_modified")
    name = fields.String(attribute="name")


class ExperimentUpdateSchema(Schema):
    __model__ = Experiment

    name = fields.String(attribute="name")


class ExperimentRegistrationFormSchema(Schema):
    __model__ = ExperimentRegistrationFormData

    name = fields.String(attribute="name", required=True)

    @pre_dump
    def extract_data_from_form(
        self, data: ExperimentRegistrationForm, many: bool, **kwargs
    ) -> Dict[str, Any]:
        def slugify(text: str) -> str:
            return text.lower().strip().replace(" ", "-")

        return {"name": slugify(data.name.data)}

    @post_dump
    def serialize_object(
        self, data: Dict[str, Any], many: bool, **kwargs
    ) -> ExperimentRegistrationFormData:
        return self.__model__(**data)  # type: ignore


ExperimentRegistrationSchema = [dict(name="name", type=str, location="form")]
