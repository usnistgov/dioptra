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
"""The data models for the queue endpoint objects."""
from __future__ import annotations

import datetime
from typing import Any

from dioptra.restapi.app import db


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
        queue: Queue | None = cls.query.order_by(cls.queue_id.desc()).first()

        if queue is None:
            return 1

        return int(queue.queue_id) + 1

    def update(self, changes: dict[str, Any]) -> Queue:
        """Updates the record.

        Args:
            changes: A dictionary containing record updates.
        """
        self.last_modified = datetime.datetime.now()

        for key, val in changes.items():
            setattr(self, key, val)

        return self
