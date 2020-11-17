import datetime

from typing_extensions import TypedDict


class QueueInterface(TypedDict, total=False):
    queue_id: int
    created_on: datetime.datetime
    last_modified: datetime.datetime
    name: str


class QueueLockInterface(TypedDict, total=False):
    queue_id: int
    created_on: datetime.datetime


class QueueUpdateInterface(TypedDict, total=False):
    name: str
    is_deleted: bool
