# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""The interfaces for creating and updating |Experiment| objects.

.. |Experiment| replace:: :py:class:`~.model.Experiment`
"""

import datetime

from typing_extensions import TypedDict


class ExperimentInterface(TypedDict, total=False):
    """The interface for constructing a new |Experiment| object.

    Attributes:
        experiment_id: An integer identifying a registered experiment.
        created_on: The date and time the experiment was created.
        last_modified: The date and time the experiment was last modified.
        name: The name of the experiment.
    """

    experiment_id: int
    created_on: datetime.datetime
    last_modified: datetime.datetime
    name: str


class ExperimentUpdateInterface(TypedDict, total=False):
    """The interface for updating an |Experiment| object.

    Attributes:
        name: The name of the experiment.
        is_deleted: A boolean that indicates if the experiment record is deleted.
    """

    name: str
    is_deleted: bool
