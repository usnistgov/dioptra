import datetime

from typing_extensions import TypedDict


class ExperimentInterface(TypedDict, total=False):
    experiment_id: int
    created_on: datetime.datetime
    last_modified: datetime.datetime
    name: str


class ExperimentUpdateInterface(TypedDict, total=False):
    name: str
