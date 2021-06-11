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
