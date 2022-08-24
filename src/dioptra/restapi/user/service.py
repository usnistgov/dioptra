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
"""The server-side functions that perform user endpoint operations."""
from __future__ import annotations

import datetime

import structlog
from injector import inject
from sqlalchemy import select
from structlog.stdlib import BoundLogger

from dioptra.restapi.app import db
from dioptra.restapi.shared.password.service import PasswordService

from .errors import UsernameNotAvailableError
from .model import User, UserRegistrationForm, UserRegistrationFormData
from .schema import UserRegistrationFormSchema

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class UserService(object):
    @inject
    def __init__(
        self,
        password_service: PasswordService,
        user_registration_form_schema: UserRegistrationFormSchema,
    ) -> None:
        self._password_service = password_service
        self._user_registration_form_schema = user_registration_form_schema

    def create(
        self,
        user_registration_form_data: UserRegistrationFormData,
        **kwargs,
    ) -> User:
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        username: str = user_registration_form_data["username"]

        if self.get_by_username(username, log=log) is not None:
            log.info("Username already exists", username=username)
            raise UsernameNotAvailableError

        timestamp = datetime.datetime.now()
        user_expire_on = datetime.datetime(9999, 12, 31, 23, 59, 59)
        password_expire_on = timestamp.replace(year=timestamp.year + 1)

        new_user: User = User(
            username=username,
            password=user_registration_form_data["password"],
            email_address=user_registration_form_data["email_address"],
            created_on=timestamp,
            last_modified_on=timestamp,
            last_login_on=timestamp,
            user_expire_on=user_expire_on,
            password_expire_on=password_expire_on,
        )
        db.session.add(new_user)
        db.session.commit()

        log.info(
            "User registration successful",
            user_id=new_user.user_id,
        )

        return new_user

    def delete(self, user_id: int, **kwargs) -> list[int]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841
        user: User | None = self.get_by_id(user_id=user_id)
        log.info("Delete user account", user_id=user_id)

        if user is None:
            log.info("User account does not exist", user_id=user_id)
            return []

        user.update(changes={"is_deleted": True})
        db.session.commit()

        log.info("User account deleted", user_id=user_id)

        return [user_id]

    @staticmethod
    def get_all(**kwargs) -> list[User]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("List all user accounts")
        stmt = select(User).filter_by(is_deleted=False)
        users: list[User] = db.session.scalars(stmt).all()

        return users

    @staticmethod
    def get_by_id(user_id: int, **kwargs) -> User | None:
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Lookup user account by unique id", user_id=user_id)
        stmt = select(User).filter_by(user_id=user_id, is_deleted=False)
        user: User | None = db.session.scalars(stmt).first()

        return user

    @staticmethod
    def get_by_username(username: str, **kwargs) -> User | None:
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Lookup user account by unique username", username=username)
        stmt = select(User).filter_by(username=username, is_deleted=False)
        user: User | None = db.session.scalars(stmt).first()

        return user

    def extract_data_from_form(
        self, user_registration_form: UserRegistrationForm, **kwargs
    ) -> UserRegistrationFormData:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        data: UserRegistrationFormData = self._user_registration_form_schema.dump(
            user_registration_form
        )

        return UserRegistrationFormData(
            username=data["username"],
            password=self._password_service.hash(data["password"]),
            email_address=data["email_address"],
        )
