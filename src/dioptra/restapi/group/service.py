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
"""The server-side functions that perform job endpoint operations."""
from __future__ import annotations

import datetime
from typing import List

import structlog
from sqlalchemy.exc import IntegrityError
from structlog.stdlib import BoundLogger

from dioptra.restapi.app import db

from .model import Group

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class GroupService(object):
    @staticmethod
    def create(name: str, user_id=None, **kwargs) -> Group:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841
        timestamp = datetime.datetime.now()

        # #to be used when user is fully implemented
        # if user_id is None:
        #     user_id= current_user.id

        return Group(
            group_id=Group.next_id(),
            name=name,
            creator_id=user_id,
            owner_id=user_id,
            created_on=timestamp,
            deleted=False,
        )

    @staticmethod
    def get_all(**kwargs) -> List[Group]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return Group.query.all()  # type: ignore

    @staticmethod
    def get_by_id(group_id: int, **kwargs) -> Group:
    def get_by_id(group_id: int, **kwargs) -> Group:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return Group.query.get(group_id)  # type: ignore

    def submit(self, name: str, user_id=None, **kwargs) -> Group:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        new_group: Group = self.create(name, user_id, log=log)

        db.session.add(new_group)
        db.session.commit()

        log.info("Group submission successful", group_id=new_group.group_id)

        return new_group

    def delete(self, id: int, **kwargs) -> bool:
        group = self.get_by_id(id)
        group.deleted = True
        try:
            db.session.commit()

            return True
        except IntegrityError:
            db.session.rollback()
            return False
