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
.. |ExperimentRegistrationForm| replace:: :py:class:`~.model.ExperimentRegistrationForm`
.. |ExperimentRegistrationFormData| replace:: \
   :py:class:`~.model.ExperimentRegistrationFormData`
"""
from __future__ import annotations

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
