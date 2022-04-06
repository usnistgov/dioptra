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
"""The data models for the job endpoint objects."""
from __future__ import annotations

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
    """The jobs table.

    Attributes:
        job_id: A UUID that identifies the job.
        mlflow_run_id: A UUID that identifies the MLFlow run associated with the job.
        experiment_id: An integer identifying a registered experiment.
        queue_id: An integer identifying a registered queue.
        created_on: The date and time the job was created.
        last_modified: The date and time the job was last modified.
        timeout: The maximum alloted time for a job before it times out and is stopped.
        workflow_uri: The URI pointing to the tarball archive or zip file uploaded with
            the job.
        entry_point: The name of the entry point in the MLproject file to run.
        entry_point_kwargs: A string listing parameter values to pass to the entry point
            for the job. The list of parameters is specified using the following format:
            `-P param1=value1 -P param2=value2`.
        status: The current status of the job. The allowed values are: `queued`,
            `started`, `deferred`, `finished`, `failed`.
        depends_on: A UUID for a previously submitted job to set as a dependency for the
            current job.
    """

    __tablename__ = "jobs"

    job_id = db.Column(db.String(36), primary_key=True)
    """A UUID that identifies the job."""

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
        """Updates the record.

        Args:
            changes: A :py:class:`~.interface.JobUpdateInterface` dictionary containing
                record updates.
        """
        self.last_modified = datetime.datetime.now()

        for key, val in changes.items():
            setattr(self, key, val)

        return self


class JobForm(FlaskForm):
    """The job submission form.

    Attributes:
        experiment_name: The name of a registered experiment.
        queue: The name of an active queue.
        timeout: The maximum alloted time for a job before it times out and is stopped.
            If omitted, the job timeout will default to 24 hours.
        entry_point: The name of the entry point in the MLproject file to run.
        entry_point_kwargs: A list of entry point parameter values to use for the job.
            The list is a string with the following format: `-P param1=value1
            -P param2=value2`. If omitted, the default values in the MLproject file will
            be used.
        depends_on: A job UUID to set as a dependency for this new job. The new job will
            not run until this job completes successfully. If omitted, then the new job
            will start as soon as computing resources are available.
        workflow: A tarball archive or zip file containing, at a minimum, a MLproject
            file and its associated entry point scripts.
    """

    experiment_name = StringField(
        "Name of Experiment",
        validators=[InputRequired()],
        description="The name of a registered experiment.",
    )
    queue = StringField(
        "Queue", validators=[InputRequired()], description="The name of an active queue"
    )
    timeout = StringField(
        "Job Timeout",
        validators=[OptionalField(), Regexp(r"\d+?[dhms]")],
        description="The maximum alloted time for a job before it times out and "
        "is stopped. If omitted, the job timeout will default to 24 hours.",
    )
    entry_point = StringField(
        "MLproject Entry Point",
        validators=[InputRequired()],
        description="The name of the entry point in the MLproject file to run.",
    )
    entry_point_kwargs = StringField(
        "MLproject Parameter Overrides",
        validators=[OptionalField()],
        description="A list of entry point parameter values to use for the job. The "
        'list is a string with the following format: "-P param1=value1 '
        '-P param2=value2". If omitted, the default values in the MLproject file will '
        "be used.",
    )
    depends_on = StringField(
        "Job Dependency",
        validators=[OptionalField(), UUID()],
        description="A job UUID to set as a dependency for this new job. The new job "
        "will not run until this job completes successfully. If omitted, then the new "
        "job will start as soon as computing resources are available.",
    )
    workflow = FileField(
        validators=[
            FileRequired(),
            FileAllowed(["tar", "tgz", "bz2", "gz", "xz", "zip"]),
        ],
        description="A tarball archive or zip file containing, at a minimum, a "
        "MLproject file and its associated entry point scripts.",
    )

    def validate_experiment_name(self, field):
        """Validates that the experiment is registered and not deleted.

        Args:
            field: The form field for `experiment_name`.
        """
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
        """Validates that the queue is registered, active and not deleted.

        Args:
            field: The form field for `queue`.
        """
        from mitre.securingai.restapi.models import Queue, QueueLock

        def slugify(text: str) -> str:
            return text.lower().strip().replace(" ", "-")

        standardized_name: str = slugify(field.data)
        queue: Optional[Queue] = (
            Queue.query.outerjoin(QueueLock, Queue.queue_id == QueueLock.queue_id)
            .filter(
                Queue.name == standardized_name,
                QueueLock.queue_id == None,  # noqa: E711
                Queue.is_deleted == False,  # noqa: E712
            )
            .first()
        )

        if queue is None:
            raise ValidationError(
                f"Bad Request - The queue {standardized_name} is not valid. "
                "Please check spelling and resubmit."
            )


class JobFormData(TypedDict, total=False):
    """The data extracted from the job submission form.

    Attributes:
        experiment_id: An integer identifying the registered experiment.
        experiment_name: The name of the registered experiment.
        queue_id: An integer identifying a registered queue.
        queue: The name of an active queue.
        timeout: The maximum alloted time for a job before it times out and is stopped.
        entry_point: The name of the entry point in the MLproject file to run.
        entry_point_kwargs: A list of entry point parameter values to use for the job.
            The list is a string with the following format: `-P param1=value1
            -P param2=value2`.
        depends_on: A job UUID to set as a dependency for this new job. The new job will
            not run until this job completes successfully.
        workflow: A tarball archive or zip file containing, at a minimum, a MLproject
            file and its associated entry point scripts.
    """

    experiment_id: int
    experiment_name: str
    queue_id: int
    queue: str
    timeout: Optional[str]
    entry_point: str
    entry_point_kwargs: Optional[str]
    depends_on: Optional[str]
    workflow: FileStorage
