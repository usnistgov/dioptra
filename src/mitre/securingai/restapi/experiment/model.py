import datetime

from flask_wtf import FlaskForm
from typing_extensions import TypedDict
from wtforms.fields import StringField
from wtforms.validators import InputRequired, ValidationError

from mitre.securingai.restapi.app import db

from .interface import ExperimentUpdateInterface


class Experiment(db.Model):  # type: ignore
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
        self.last_modified = datetime.datetime.now()

        for key, val in changes.items():
            setattr(self, key, val)

        return self


class ExperimentRegistrationForm(FlaskForm):
    name = StringField("Name of Experiment", validators=[InputRequired()])

    def validate_name(self, field):
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
    name: str
