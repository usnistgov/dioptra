import datetime
from typing import Optional

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from typing_extensions import TypedDict
from werkzeug.datastructures import FileStorage
from wtforms.fields import StringField
from wtforms.validators import UUID, InputRequired
from wtforms.validators import Optional as OptionalField
from wtforms.validators import Regexp, ValidationError

from mitre.securingai.restapi.app import db

from .interface import JobUpdateInterface

job_statuses = db.Table(
    "job_statuses", db.Column("status", db.String(255), primary_key=True)
)


class Job(db.Model):
    __tablename__ = "jobs"

    job_id = db.Column(db.String(36), primary_key=True)
    mlflow_run_id = db.Column(db.String(36), index=True)
    experiment_id = db.Column(
        db.BigInteger(), db.ForeignKey("experiments.experiment_id"), index=True
    )
    queue_id = db.Column(db.BigInteger(), db.ForeignKey("queues.queue_id"), index=True)
    created_on = db.Column(db.DateTime())
    last_modified = db.Column(db.DateTime())
    timeout = db.Column(db.Text())
    workflow_uri = db.Column(db.Text())
    entry_point = db.Column(db.Text())
    entry_point_kwargs = db.Column(db.Text())
    status = db.Column(
        db.String(255),
        db.ForeignKey("job_statuses.status"),
        default="queued",
        index=True,
    )
    depends_on = db.Column(db.String(36))

    experiment = db.relationship("Experiment", back_populates="jobs")
    queue = db.relationship("Queue", back_populates="jobs")

    def update(self, changes: JobUpdateInterface):
        self.last_modified = datetime.datetime.now()

        for key, val in changes.items():
            setattr(self, key, val)

        return self


class JobForm(FlaskForm):
    experiment_name = StringField("Name of Experiment", validators=[InputRequired()])
    queue = StringField("Queue", validators=[InputRequired()])
    timeout = StringField(
        "Job Timeout", validators=[OptionalField(), Regexp(r"\d+?[dhms]")]
    )
    entry_point = StringField("MLproject Entry Point", validators=[InputRequired()])
    entry_point_kwargs = StringField(
        "MLproject Parameter Overrides", validators=[OptionalField()]
    )
    depends_on = StringField("Job Dependency", validators=[OptionalField(), UUID()])
    workflow = FileField(
        validators=[
            FileRequired(),
            FileAllowed(["tar", "tgz", "bz2", "gz", "xz", "zip"]),
        ]
    )

    def validate_experiment_name(self, field):
        from mitre.securingai.restapi.models import Experiment

        def slugify(text: str) -> str:
            return text.lower().strip().replace(" ", "-")

        standardized_name: str = slugify(field.data)

        if (
            Experiment.query.filter_by(name=standardized_name, is_deleted=False).first()
            is None
        ):
            raise ValidationError(
                f"Bad Request - The experiment {standardized_name} does not exist. "
                "Please check spelling and resubmit."
            )

    def validate_queue(self, field):
        from mitre.securingai.restapi.models import Queue, QueueLock

        def slugify(text: str) -> str:
            return text.lower().strip().replace(" ", "-")

        standardized_name: str = slugify(field.data)
        queue: Optional[Queue] = (
            Queue.query.outerjoin(QueueLock, Queue.queue_id == QueueLock.queue_id)
            .filter(
                Queue.name == standardized_name,
                QueueLock.queue_id == None,  # noqa: E711
                Queue.is_deleted == False,
            )
            .first()
        )

        if queue is None:
            raise ValidationError(
                f"Bad Request - The queue {standardized_name} is not valid. "
                "Please check spelling and resubmit."
            )


class JobFormData(TypedDict, total=False):
    experiment_id: int
    experiment_name: str
    queue_id: int
    queue: str
    timeout: Optional[str]
    entry_point: str
    entry_point_kwargs: Optional[str]
    depends_on: Optional[str]
    workflow: FileStorage
