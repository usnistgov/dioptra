"""The schemas for serializing/deserializing the experiment endpoint objects.

.. |Experiment| replace:: :py:class:`~.model.Experiment`
.. |ExperimentRegistrationForm| replace:: :py:class:`~.model.ExperimentRegistrationForm`
.. |ExperimentRegistrationFormData| replace:: \
   :py:class:`~.model.ExperimentRegistrationFormData`
"""

from typing import Any, Dict

from marshmallow import Schema, fields, post_dump, pre_dump

from .model import (
    Experiment,
    ExperimentRegistrationForm,
    ExperimentRegistrationFormData,
)


class ExperimentSchema(Schema):
    """The schema for the data stored in an |Experiment| object.

    Attributes:
        experimentId: An integer identifying a registered experiment.
        createdOn: The date and time the experiment was created.
        lastModified: The date and time the experiment was last modified.
        name: The name of the experiment.
    """

    __model__ = Experiment

    experimentId = fields.Integer(
        attribute="experiment_id",
        metadata=dict(description="An integer identifying a registered experiment."),
    )
    createdOn = fields.DateTime(
        attribute="created_on",
        metadata=dict(description="The date and time the experiment was created."),
    )
    lastModified = fields.DateTime(
        attribute="last_modified",
        metadata=dict(
            description="The date and time the experiment was last modified."
        ),
    )
    name = fields.String(
        attribute="name", metadata=dict(description="The name of the experiment.")
    )


class ExperimentUpdateSchema(Schema):
    """The schema for the data used to update an |Experiment| object.

    Attributes:
        name: The new name of the experiment. Must be unique.
    """

    __model__ = Experiment

    name = fields.String(
        attribute="name",
        metadata=dict(description="The new name of the experiment. Must be unique."),
    )


class ExperimentRegistrationFormSchema(Schema):
    """The schema for the information stored in an experiment registration form.

    Attributes:
        name: The name of the experiment. Must be unique.
    """

    __model__ = ExperimentRegistrationFormData

    name = fields.String(
        attribute="name",
        required=True,
        metadata=dict(description="The name of the experiment. Must be unique."),
    )

    @pre_dump
    def extract_data_from_form(
        self, data: ExperimentRegistrationForm, many: bool, **kwargs
    ) -> Dict[str, Any]:
        """Extracts data from the |ExperimentRegistrationForm| for validation."""

        def slugify(text: str) -> str:
            return text.lower().strip().replace(" ", "-")

        return {"name": slugify(data.name.data)}

    @post_dump
    def serialize_object(
        self, data: Dict[str, Any], many: bool, **kwargs
    ) -> ExperimentRegistrationFormData:
        """Makes an |ExperimentRegistrationFormData| object from the validated data."""
        return self.__model__(**data)  # type: ignore


ExperimentRegistrationSchema = [
    dict(
        name="name",
        type=str,
        location="form",
        required=True,
        help="The name of the experiment. Must be unique.",
    )
]
