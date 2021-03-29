"""The data models for the queue endpoint objects."""

from __future__ import annotations

import datetime
from typing import Optional

from flask_wtf import FlaskForm
from typing_extensions import TypedDict
from wtforms.fields import StringField
from wtforms.validators import InputRequired, ValidationError

from mitre.securingai.restapi.app import db

from .interface import QueueUpdateInterface


class QueueLock(db.Model):
    """The queue_locks table.

    Attributes:
        queue_id: An integer identifying a registered queue.
        created_on: The date and time the queue lock was created.
    """

    __tablename__ = "queue_locks"

    queue_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        db.ForeignKey("queues.queue_id"),
        primary_key=True,
    )
    created_on = db.Column(db.DateTime(), default=datetime.datetime.now)

    queue = db.relationship("Queue", back_populates="lock")


class Queue(db.Model):
    """The queues table.

    Attributes:
        queue_id: An integer identifying a registered queue.
        created_on: The date and time the queue was created.
        last_modified: The date and time the queue was last modified.
        name: The name of the queue.
        is_deleted: A boolean that indicates if the queue record is deleted.
    """

    __tablename__ = "queues"

    queue_id = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"), primary_key=True
    )
    created_on = db.Column(db.DateTime())
    last_modified = db.Column(db.DateTime())
    name = db.Column(db.Text(), index=True, nullable=False, unique=True)
    is_deleted = db.Column(db.Boolean(), default=False)

    jobs = db.relationship("Job", back_populates="queue", lazy="dynamic")
    lock = db.relationship("QueueLock", back_populates="queue")

    @classmethod
    def next_id(cls) -> int:
        """Generates the next id in the sequence."""
        queue: Optional[Queue] = cls.query.order_by(cls.queue_id.desc()).first()

        if queue is None:
            return 1

        return int(queue.queue_id) + 1

    def update(self, changes: QueueUpdateInterface):
        """Updates the record.

        Args:
            changes: A :py:class:`~.interface.QueueUpdateInterface` dictionary
                containing record updates.
        """
        self.last_modified = datetime.datetime.now()

        for key, val in changes.items():
            setattr(self, key, val)

        return self


class QueueRegistrationForm(FlaskForm):
    """The queue registration form.

    Attributes:
        name: The name to register as a new queue.
    """

    name = StringField(
        "Name of Queue",
        validators=[InputRequired()],
        description="The name to register as a new queue.",
    )

    def validate_name(self, field):
        """Validates that the queue does not exist in the registry.

        Args:
            field: The form field for `name`.
        """

        def slugify(text: str) -> str:
            return text.lower().strip().replace(" ", "-")

        standardized_name: str = slugify(field.data)

        if (
            Queue.query.filter_by(name=standardized_name, is_deleted=False).first()
            is not None
        ):
            raise ValidationError(
                "Bad Request - A queue is already registered under the name "
                f"{standardized_name}. Please select another and resubmit."
            )


class QueueRegistrationFormData(TypedDict, total=False):
    """The data extracted from the queue registration form.

    Attributes:
        name: The name of the queue.
    """

    name: str
