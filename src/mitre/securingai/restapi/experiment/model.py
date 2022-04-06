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
"""The data models for the experiment endpoint objects."""
from __future__ import annotations

import datetime

from flask_wtf import FlaskForm
from typing_extensions import TypedDict
from wtforms.fields import StringField
from wtforms.validators import InputRequired, ValidationError

from mitre.securingai.restapi.app import db

from .interface import ExperimentUpdateInterface


class Experiment(db.Model):
    """The experiments table.

    Attributes:
        experiment_id: An integer identifying a registered experiment.
        created_on: The date and time the experiment was created.
        last_modified: The date and time the experiment was last modified.
        name: The name of the experiment.
        is_deleted: A boolean that indicates if the experiment record is deleted.
    """

    __tablename__ = "experiments"

    experiment_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True
    )
    created_on = db.Column(db.DateTime())
    last_modified = db.Column(db.DateTime())
    name = db.Column(db.Text(), index=True, nullable=False, unique=True)
    is_deleted = db.Column(db.Boolean(), default=False)

    jobs = db.relationship("Job", back_populates="experiment")

    def update(self, changes: ExperimentUpdateInterface):
        """Updates the record.

        Args:
            changes: A :py:class:`~.interface.ExperimentUpdateInterface` dictionary
                containing record updates.
        """
        self.last_modified = datetime.datetime.now()

        for key, val in changes.items():
            setattr(self, key, val)

        return self


class ExperimentRegistrationForm(FlaskForm):
    """The experiment registration form.

    Attributes:
        name: The name to register as a new experiment.
    """

    name = StringField("Name of Experiment", validators=[InputRequired()])

    def validate_name(self, field):
        """Validates that the experiment does not exist in the registry.

        Args:
            field: The form field for `name`.
        """

        def slugify(text: str) -> str:
            return text.lower().strip().replace(" ", "-")

        standardized_name: str = slugify(field.data)

        if (
            Experiment.query.filter_by(name=standardized_name, is_deleted=False).first()
            is not None
        ):
            raise ValidationError(
                "Bad Request - An experiment is already registered under "
                f"the name {standardized_name}. Please select another and resubmit."
            )


class ExperimentRegistrationFormData(TypedDict, total=False):
    """The data extracted from the experiment registration form.

    Attributes:
        name: The name of the experiment.
    """

    name: str
