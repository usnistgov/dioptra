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
import uuid
from typing import Any, Final, cast

import structlog
from flask_login import current_user
from injector import inject
from passlib.hash import pbkdf2_sha256
from sqlalchemy import select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.v1.groups.service import GroupService

from .errors import (
    NoCurrentUserError,
    UserDoesNotExistError,
    UserEmailNotAvailableError,
    UsernameNotAvailableError,
    UserPasswordChangeError,
    UserPasswordExpiredError,
    UserPasswordVerificationError,
    UserRegistrationError,
)

# from dioptra.restapi.v1.shared.password.service import PasswordService

# from dioptra.restapi.v1 import search_parser


LOGGER: BoundLogger = structlog.stdlib.get_logger()

DAYS_TO_EXPIRE_PASSWORD_DEFAULT: Final[int] = 365


class UserService(object):
    """The service methods used to register and manage user accounts."""

    @inject
    def __init__(
        self,
        user_password_service: UserPasswordService,
        user_name_service: UserNameService,
        group_service: GroupService,
    ) -> None:
        """Initialize the user service.

        All arguments are provided via dependency injection.

        Args:
            user_password_service: A UserPasswordService object.
            user_name_service: A UserNameService object.
            group_service: A GroupService object.
        """
        self._user_password_service = user_password_service
        self._user_name_service = user_name_service
        self._group_service = group_service

    def create(
        self,
        username: str,
        email_address: str,
        password: str,
        confirm_password: str,
        **kwargs,
    ) -> models.User:
        """Create a new user.

        Args:
            username: The username requested by the new user. Must be unique.
            email_address: The email address to associate with the new user.
            password: The password for the new user.
            confirm_password: The password confirmation for the new user.

        Returns:
            The new user object.

        Raises:
            UserRegistrationError: If the password and confirmation password do not
                match.
            UsernameNotAvailableError: If the username already exists.
            UserEmailNotAvailableError: If the email already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if password != confirm_password:
            raise UserRegistrationError(
                "The password and confirmation password did not match."
            )

        if self._user_name_service.get(username, log=log) is not None:
            log.info("Username already exists", username=username)
            raise UsernameNotAvailableError

        if self._get_user_by_email(email_address, log=log) is not None:
            log.info("Email already exists", email_address=email_address)
            raise UserEmailNotAvailableError

        stmt = select(models.Group).filter_by(name="public")
        public_group: models.Group | None = db.session.scalars(stmt).first()

        hashed_password = self._user_password_service.hash(password, log=log)
        new_user: models.User = models.User(
            username=username, password=hashed_password, email_address=email_address
        )

        if public_group is None:
            public_group = models.Group(name="public", creator=new_user)

        public_group.managers.append(
            models.GroupManager(user=new_user, owner=True, admin=True)
        )
        public_group.members.append(
            models.GroupMember(
                user=new_user,
                read=True,
                write=True,
                share_read=True,
                share_write=True,
            )
        )

        personal_group: models.Group = models.Group(
            name=new_user.username, creator=new_user
        )
        personal_group.managers.append(
            models.GroupManager(user=new_user, owner=True, admin=True)
        )
        personal_group.members.append(
            models.GroupMember(
                user=new_user,
                read=True,
                write=True,
                share_read=True,
                share_write=True,
            )
        )

        db.session.add(public_group)
        db.session.add(personal_group)
        db.session.add(new_user)
        db.session.commit()

        log.info("User registration successful", user_id=new_user.user_id)

        return new_user

    def get(
        self,
        search_string: str,
        page_index: int,
        page_length: int,
        **kwargs,
    ) -> list[models.User]:
        """Fetch a list of users, optionally filtering by search string and paging
        parameters.

        Args:
            search_string: A search string used to filter results.
            page_index: The index of the first user to be returned.
            page_length: The maximum number of users to be returned.

        Returns:
            A paging envelope containing a list of fetched users.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Get list of users")

        pattern = search_string or "%"

        stmt = (
            select(models.User)
            .where(models.User.username.like(pattern))
            .offset(page_index)
            .limit(page_length + 1)
        )
        users = db.session.scalars(stmt).all()

        return list(users)

    def _get_user_by_email(
        self, email_address: str, error_if_not_found: bool = False, **kwargs
    ) -> models.User | None:
        """Fetch a user by its email address.

        Args:
            email_address: The email addressof the user.
            error_if_not_found: If True, raise an error if the user is not found.
                Defaults to False.

        Returns:
            The user object if found, otherwise None.

        Raises:
            UserDoesNotExistError: If the user is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Lookup user account by email", email_address=email_address)

        stmt = select(models.User).filter_by(
            email_address=email_address, is_deleted=False
        )
        user: models.User | None = db.session.scalars(stmt).first()

        if user is None:
            if error_if_not_found:
                log.error("User not found", email_address=email_address)
                raise UserDoesNotExistError

            return None

        return user


class UserIdService(object):
    """The service methods used to manage a user by ID."""

    @inject
    def __init__(
        self,
        user_password_service: UserPasswordService,
    ) -> None:
        """Initialize the current user service.

        All arguments are provided via dependency injection.

        Args:
            user_password_service: A UserPasswordService object.
        """
        self._user_password_service = user_password_service

    def get(
        self, user_id: int, error_if_not_found: bool = False, **kwargs
    ) -> models.User | None:
        """Fetch a user by its unique id.

        Args:
            user_id: The unique id of the user.
            error_if_not_found: If True, raise an error if the user is not found.
                Defaults to False.

        Returns:
            The user object if found, otherwise None.

        Raises:
            UserDoesNotExistError: If the user is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Lookup user account by unique id", user_id=user_id)

        stmt = select(models.User).filter_by(user_id=user_id, is_deleted=False)
        user: models.User | None = db.session.scalars(stmt).first()

        if user is None:
            if error_if_not_found:
                log.error("User not found", user_id=user_id)
                raise UserDoesNotExistError

            return None

        return user

    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
        confirm_new_password: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Change the current user's password.

        Args:
            current_password: The user's current password.
            new_password: The user's new password, to replace the current one after
                authentication.
            confirm_new_password: Confirmation of the new password.

        Returns:
            A dictionary containing the password change success message if the password
            change is successful.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Change a user's password by ID.", user_id=user_id)
        user = cast(
            models.User, self.get(user_id=user_id, error_if_not_found=True, log=log)
        )
        return self._user_password_service.change(
            user=user,
            current_password=current_password,
            new_password=new_password,
            confirm_new_password=confirm_new_password,
            log=log,
        )


class UserCurrentService(object):
    """The service methods used to manage the current user."""

    @inject
    def __init__(
        self,
        user_id_service: UserIdService,
        user_password_service: UserPasswordService,
    ) -> None:
        """Initialize the current current user service.

        All arguments are provided via dependency injection.

        Args:
            user_id_service: A UserIdService object.
            user_password_service: A UserPasswordService object.
        """
        self._user_id_service = user_id_service
        self._user_password_service = user_password_service

    def get(self, **kwargs) -> models.User:
        """Fetch information about the current user.

        Returns:
            The current user object.

        Raises:
            NoCurrentUserError: If there is no current user.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if not current_user.is_authenticated:
            log.error("There is no current user.")
            raise NoCurrentUserError

        return cast(models.User, current_user)

    def modify(self, username: str, email_address: str, **kwargs) -> models.User:
        """Modifies the current user

        Args:
            username: The user's current username.
            email_address: The user's current email_address.

        Returns:
            The current user object.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Modify user account", user_id=current_user.user_id)

        if username != current_user.username:
            stmt = select(models.Group).filter_by(name=current_user.username)
            personal_group: models.Group | None = db.session.scalars(stmt).first()
            if (
                personal_group is not None
                and personal_group.creator.user_id == current_user.user_id
            ):
                personal_group.name = username

        current_user.username = username
        current_user.email_address = email_address
        db.session.commit()

        return cast(models.User, current_user)

    def delete(self, password: str, **kwargs) -> dict[str, Any]:
        """Permanently deletes the current user.

        Args:
            password: The current user's password.

        Returns:
            A dictionary containing the delete user success message if the user is
            deleted successfully.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Delete user account", user_id=current_user.user_id)
        self._user_password_service.authenticate(
            password=password,
            user_password=current_user.password,
            expiration_date=current_user.password_expire_on,
            error_if_failed=True,
            log=log,
        )

        username = current_user.username

        deleted_user_lock = models.UserLock(
            user_lock_type="delete",
            user=current_user,
        )
        db.session.add(deleted_user_lock)
        db.session.commit()
        log.info("User account deleted", user_id=current_user.user_id)

        return {"status": "Success", "username": [username]}

    def change_password(
        self,
        current_password: str,
        new_password: str,
        confirm_new_password: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Change the current user's password.

        Args:
            current_password: The user's current password.
            new_password: The user's new password, to replace the current one after
                authentication.
            confirm_new_password: Confirmation of the new password.

        Returns:
            A dictionary containing the password change success message if the password
            change is successful.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Change the current user's password", user_id=current_user.user_id)
        return self._user_password_service.change(
            user=current_user,
            current_password=current_password,
            new_password=new_password,
            confirm_new_password=confirm_new_password,
            log=log,
        )


class UserNameService(object):
    """The service methods used to register and manage user accounts by username."""

    @inject
    def __init__(
        self,
        user_password_service: UserPasswordService,
    ) -> None:
        """Initialize the user name service.

        All arguments are provided via dependency injection.

        Args:
            user_password_service: A UserPasswordService object.
        """
        self._user_password_service = user_password_service

    def get(
        self, username: str, error_if_not_found: bool = False, **kwargs
    ) -> models.User | None:
        """Fetch a user by its username.

        Args:
            username: The username of the user.
            error_if_not_found: If True, raise an error if the user is not found.
                Defaults to False.

        Returns:
            The user object if found, otherwise None.

        Raises:
            UserDoesNotExistError: If the user is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Lookup user account by unique username", username=username)

        stmt = select(models.User).filter_by(username=username, is_deleted=False)
        user: models.User | None = db.session.scalars(stmt).first()

        if user is None:
            if error_if_not_found:
                log.error("User not found", username=username)
                raise UserDoesNotExistError

            return None

        return user


class UserPasswordService(object):
    """The service methods used to manage user passwords."""

    @inject
    def __init__(
        self,
        password_service: PasswordService,
    ) -> None:
        """Initialize the user password service.

        All arguments are provided via dependency injection.

        Args:
            password_service: A PasswordService object.
        """
        self._password_service = password_service

    def authenticate(
        self,
        password: str,
        user_password: str,
        expiration_date: datetime.datetime,
        error_if_failed: bool = False,
        **kwargs,
    ) -> bool:
        """Authenticate a user's password.

        Args:
            password: The password to verify.
            user_password: The user's hashed password.
            expiration_date: The date and time the user's password is set to expire.
            error_if_failed: If True, raise an error if the password verification fails.
                Defaults to False.

        Returns:
            True if the password is verified, otherwise False.

        Raises:
            UserPasswordVerificationError: If the password verification fails and
                `error_if_failed` is True.
            UserPasswordExpiredError: If the user's password has expired.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        current_timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        authenticated = self._password_service.verify(
            password=password, hashed_password=user_password, log=log
        )

        if not authenticated and error_if_failed:
            log.error("Password authentication failed.")
            raise UserPasswordVerificationError

        if expiration_date < current_timestamp:
            log.error("Password expired")
            raise UserPasswordExpiredError

        return authenticated

    def change(
        self,
        user: models.User,
        current_password: str,
        new_password: str,
        confirm_new_password: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Change a user's password.

        Args:
            user: The user object.
            current_password: The user's current password.
            new_password: The user's new password, to replace the current one after
                authentication.
            confirm_new_password: Confirmation of the new password.

        Returns:
            A dictionary containing the password change success message if the password
            change is successful.

        Raises:
            UserPasswordChangeError: If the password change fails.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if not self._password_service.verify(
            password=current_password, hashed_password=str(user.password), log=log
        ):
            raise UserPasswordChangeError

        log.info("pw", new=new_password, conf=confirm_new_password)
        if new_password != confirm_new_password:
            raise UserPasswordChangeError

        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        user.password = self._password_service.hash(password=new_password, log=log)
        user.alternative_id = uuid.uuid4()
        user.last_modified_on = timestamp
        user.password_expire_on = timestamp + datetime.timedelta(
            days=DAYS_TO_EXPIRE_PASSWORD_DEFAULT
        )

        db.session.commit()

        return {"status": "Password Change Success", "username": [user.username]}

    def hash(self, password: str, **kwargs) -> str:
        """Hash a password.

        Args:
            password: The password to hash.

        Returns:
            The hashed password.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        return self._password_service.hash(password=password, log=log)


class PasswordService(object):
    def hash(self, password: str, **kwargs) -> str:
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Hashing password")
        return str(pbkdf2_sha256.hash(password))

    def verify(self, password: str, hashed_password: str, **kwargs) -> bool:
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Verifying password")

        return bool(pbkdf2_sha256.verify(password, hashed_password))
