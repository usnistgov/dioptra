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
import contextlib
from types import TracebackType
from typing import Literal, Type

from dioptra.restapi.db.db import db
from dioptra.restapi.db.repository.drafts import DraftsRepository
from dioptra.restapi.db.repository.experiments import ExperimentRepository
from dioptra.restapi.db.repository.groups import GroupRepository
from dioptra.restapi.db.repository.queues import QueueRepository
from dioptra.restapi.db.repository.types import TypeRepository
from dioptra.restapi.db.repository.users import UserRepository


class UnitOfWork(contextlib.AbstractContextManager):
    """
    A class whose instances act as a focal point for data operations.
    Instances can commit/rollback transactions; they are also usable as
    context managers which manage transactions automatically.  One can access
    repositories via attributes on the instance.
    """

    def __init__(self) -> None:
        self.session = db.session
        self.user_repo = UserRepository(self.session)
        self.group_repo = GroupRepository(self.session)
        self.queue_repo = QueueRepository(self.session)
        self.drafts_repo = DraftsRepository(self.session)
        self.experiment_repo = ExperimentRepository(self.session)
        self.type_repo = TypeRepository(self.session)

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        # Rollback if exiting due to a thrown exception
        if exc_type:
            self.rollback()
        else:
            self.commit()

        return False
