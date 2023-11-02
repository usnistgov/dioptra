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

from dioptra.restapi.app import db
from dioptra.restapi.utils import slugify

from .interface import JobUpdateInterface

from ..SharedResource import SharedResource

job_statuses = db.Table(
    "job_statuses", db.Column("status", db.String(255), primary_key=True)
)


class Resource(db.Model):
    """The Resource table.

    Attributes:
        resource_id: A UUID that identifies the resource.
        creator_id: A UUID that identifies the user that created the resource.
        owner_id:  A UUID that identifies the group that owns the resource.
        created_on: The date and time the resource was created.
        last_modified: The date and time the resource was last modified.
    """

    __tablename__ = "Resources"

    resource_id = db.Column(db.String(36), primary_key=True)
    """A UUID that identifies the Resource."""

    creator_id = db.Column(db.BigInteger(), db.ForeignKey("users.user_id"), index=True)
    owner_id = db.Column(db.BigInteger(), db.ForeignKey("groups.group_id"), index=True)
    created_on = db.Column(db.DateTime())
    last_modified = db.Column(db.DateTime())
    deleted = db.Column(db.Boolean)

    creator = db.relationship("User", foreign_keys=[creator_id])
    owner = db.relationship("Group", foreign_keys=[owner_id])

    @property
    def shares(self):
        """List of groups that the resource is shared with."""
        # Define a relationship with SharedPrototypeResource, if needed
        return SharedResource.query.filter_by(resource_id=self.resource_id).all()

    def check_permission(self, user: User, action: str) -> bool:
        """Check if the user has permission to perform the specified action.

        Args:
            user: The user to check.
            action: The action to check.

        Returns:
            True if the user has permission to perform the action, False otherwise.
        """

        membership = GroupMemberships.query.filter_by(user_id=user.user_id)
        # next((x for x in self.owner.users if x.user_id == user.id), None)

        if membership is None:
            return False

        return cast(bool, getattr(membership, action))

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

    def validate_experiment_name(self, field: StringField) -> None:
        """Validates that the experiment is registered and not deleted.

        Args:
            field: The form field for `experiment_name`.
        """
        from dioptra.restapi.models import Experiment

        standardized_name: str = slugify(field.data)

        if (
            Experiment.query.filter_by(name=standardized_name, is_deleted=False).first()
            is None
        ):
            raise ValidationError(
                f"Bad Request - The experiment {standardized_name} does not exist. "
                "Please check spelling and resubmit."
            )

    def validate_queue(self, field: StringField) -> None:
        """Validates that the queue is registered, active and not deleted.

        Args:
            field: The form field for `queue`.
        """
        from dioptra.restapi.models import Queue, QueueLock

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
