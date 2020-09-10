import datetime
from typing import BinaryIO, Optional, Union

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from typing_extensions import TypedDict
from werkzeug.datastructures import FileStorage
from wtforms.fields import SelectField, StringField
from wtforms.validators import Regexp, UUID
from wtforms.validators import Optional as OptionalField

from .interface import JobUpdateInterface
from mitre.securingai.restapi.app import db
from mitre.securingai.restapi.shared.job_queue.model import JobQueue, JobStatus


class JobForm(FlaskForm):
    queue = SelectField(
        "Queue",
        choices=[
            (JobQueue.tensorflow_cpu.name, "Tensorflow (CPU)"),
            (JobQueue.tensorflow_gpu.name, "Tensorflow (GPU)"),
        ],
    )
    timeout = StringField(
        "Job Timeout", validators=[OptionalField(), Regexp(r"\d+?[dhms]")]
    )
    entry_point = StringField("MLproject Entry Point")
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


class JobFormData(TypedDict, total=False):
    queue: JobQueue
    timeout: Optional[str]
    entry_point: str
    entry_point_kwargs: Optional[str]
    depends_on: Optional[str]
    workflow: Union[BinaryIO, FileStorage]


class Job(db.Model):  # type: ignore
    __tablename__ = "jobs"

    job_id = db.Column(db.String(36), primary_key=True)
    mlflow_run_id = db.Column(db.String(36), index=True)
    created_on = db.Column(db.DateTime())
    last_modified = db.Column(db.DateTime())
    queue = db.Column(db.Enum(JobQueue), index=True)
    timeout = db.Column(db.Text())
    workflow_uri = db.Column(db.Text())
    entry_point = db.Column(db.Text())
    entry_point_kwargs = db.Column(db.Text())
    depends_on = db.Column(db.String(36))
    status = db.Column(db.Enum(JobStatus), default=JobStatus.queued)

    def update(self, changes: JobUpdateInterface):
        self.last_modified = datetime.datetime.now()

        for key, val in changes.items():
            setattr(self, key, val)

        return self
