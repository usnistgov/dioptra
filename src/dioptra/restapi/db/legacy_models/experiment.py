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
"""The data models for the experiment endpoint objects."""
import datetime
from typing import TYPE_CHECKING, Any, Dict

from sqlalchemy.orm import Mapped, mapped_column, relationship

from dioptra.restapi.db.db import db, intpk, text_

if TYPE_CHECKING:
    from .job import LegacyJob


class LegacyExperiment(db.Model):  # type: ignore[name-defined]
    """The experiments table.

    Attributes:
        experiment_id: An integer identifying a registered experiment.
        created_on: The date and time the experiment was created.
        last_modified: The date and time the experiment was last modified.
        name: The name of the experiment.
        is_deleted: A boolean that indicates if the experiment record is deleted.
    """

    __tablename__ = "legacy_experiments"

    experiment_id: Mapped[intpk]
    created_on: Mapped[datetime.datetime] = mapped_column(nullable=True)
    last_modified: Mapped[datetime.datetime] = mapped_column(nullable=True)
    name: Mapped[text_] = mapped_column(nullable=False, unique=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(init=False, nullable=True)

    jobs: Mapped["LegacyJob"] = relationship(init=False, back_populates="experiment")

    def __post_init__(self) -> None:
        self.is_deleted = False

    def update(self, changes: Dict[str, Any]):
        """Updates the record.

        Args:
            changes: A :py:class:`~.interface.ExperimentUpdateInterface` dictionary
                containing record updates.
        """
        self.last_modified = datetime.datetime.now()

        for key, val in changes.items():
            setattr(self, key, val)

        return self
