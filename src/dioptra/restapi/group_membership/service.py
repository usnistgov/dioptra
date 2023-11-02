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
"""The server-side functions that perform group membership endpoint operations."""
from __future__ import annotations

from typing import List

import structlog
from sqlalchemy.exc import IntegrityError
from structlog.stdlib import BoundLogger

from dioptra.restapi.app import db

from .model import GroupMembership

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class GroupMembershipService(object):
    @staticmethod
    def create(
        group_id: int,
        user_id: int,
        read: bool,
        write: bool,
        share_read: bool,
        share_write: bool,
        **kwargs,
    ) -> GroupMembership:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841\

        return GroupMembership(
            group_id=group_id,
            user_id=user_id,
            read=read,
            write=write,
            share_read=share_read,
            share_write=share_write,
        )

    @staticmethod
    def get_all(**kwargs) -> List[GroupMembership]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return GroupMembership.query.all()  # type: ignore

    @staticmethod
    def get_by_id(group_id: int, user_id: int, **kwargs) -> GroupMembership | None:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return GroupMembership.query.filter(  # type: ignore
            GroupMembership.user_id == user_id, GroupMembership.group_id == group_id
        ).first()

    def submit(
        self,
        group_id: int,
        user_id: int,
        read: bool,
        write: bool,
        share_read: bool,
        share_write: bool,
        **kwargs,
    ) -> GroupMembership:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        new_group_membership: GroupMembership = self.create(
            group_id, user_id, read, write, share_read, share_write, log=log
        )

        db.session.add(new_group_membership)
        db.session.commit()

        log.info(
            "Group Membership submission successful",
            group_id=new_group_membership.group_id,
            user_id=new_group_membership.user_id,
        )

        return new_group_membership

    def delete(self, group_id, user_id, **kwargs) -> bool:
        membership = self.get_by_id(group_id=group_id, user_id=user_id)

        try:
            db.session.delete(membership)
            db.session.commit()

            return True
        except IntegrityError:
            db.session.rollback()
            return False
