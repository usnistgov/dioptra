# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""The interfaces for creating and updating |Queue| objects.

.. |Queue| replace:: :py:class:`~.model.Queue`
"""

import datetime

from typing_extensions import TypedDict


class QueueInterface(TypedDict, total=False):
    """The interface for constructing a new |Queue| object.

    Attributes:
        queue_id: An integer identifying a registered queue.
        created_on: The date and time the queue was created.
        last_modified: The date and time the queue was last modified.
        name: The name of the queue.
    """

    queue_id: int
    created_on: datetime.datetime
    last_modified: datetime.datetime
    name: str


class QueueLockInterface(TypedDict, total=False):
    """The interface for constructing a new |QueueLock| object.

    Attributes:
        queue_id: An integer identifying a registered queue.
        created_on: The date and time the queue lock was created.
    """

    queue_id: int
    created_on: datetime.datetime


class QueueUpdateInterface(TypedDict, total=False):
    """The interface for updating a |Queue| object.

    Attributes:
        name: The name of the queue.
        is_deleted: A boolean that indicates if the queue record is deleted.
    """

    name: str
    is_deleted: bool
