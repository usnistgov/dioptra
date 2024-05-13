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

MAX_PAGE_LENGTH = 20
DAYS_TO_EXPIRE_PASSWORD_DEFAULT: Final[int] = 365


class UserService(object):
    """The service methods used to register and manage user accounts."""

    @inject
    def __init__(
        self,
        user_password_service: UserPasswordService,
        user_name_service: UserNameService,
    ) -> None:
        """Initialize the user service.

        All arguments are provided via dependency injection.

        Args:
            user_password_service: A UserPasswordService object.
            user_name_service: A UserNameService object.
        """
        self._user_password_service = user_password_service
        self._user_name_service = user_name_service

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

        if (
            self._user_name_service.get(username, err_if_not_found=False, log=log)
            is not None
        ):
            log.info("Username already exists", username=username)
            raise UsernameNotAvailableError

        if self._get_user_by_email(email_address, log=log) is not None:
            log.info("Email already exists", email_address=email_address)
            raise UserEmailNotAvailableError

        hashed_password = self._user_password_service.hash(password, log=log)
        new_user: models.User = models.User(
            username=username, password=hashed_password, email_address=email_address
        )
        db.session.add(new_user)
        db.session.commit()

        log.info("User registration successful", user_id=new_user.user_id)

        return build_current_user(new_user)

    def get(
        self,
        search_string: str | None = None,
        page_index: int | None = None,
        page_length: int | None = None,
        **kwargs,
    ) -> dict[str:Any]:
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

        if search_string is None:
            pattern = "%"
            # search_terms = search_parser.parse_string(search)
        else:
            pattern = search_string

        if page_index is None:
            page_index = 0

        if page_length is None or page_length > MAX_PAGE_LENGTH:
            page_length = MAX_PAGE_LENGTH

        stmt = (
            select(models.User)
            .where(models.User.username.like(pattern))
            .offset(page_index)
            .limit(page_length + 1)
        )
        users = db.session.scalars(stmt).all()

        users = [build_user(user) for user in users]
        return build_paging_envelope(
            "users", users, search_string, page_index, page_length
        )

    def _get_by_email(
        self, email_address: str, error_if_not_found: bool = True, **kwargs
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

        stmt = select(models.User).filter_by(email_address=email_address)
        user: models.User | None = db.session.scalars(stmt).first()

        if not user.is_active:
            user = None

        if user is None:
            if error_if_not_found:
                log.error("User not found", email_address=email_address)
                raise UserDoesNotExistError

            return None


class UserCurrentService(object):
    """The service methods used to manage the current user."""

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

        return build_user(current_user)

    def delete(self, **kwargs) -> dict[str, Any]:
        """Permanently deletes the current user.

        Returns:
            A dictionary containing the delete user success message if the user is
            deleted successfully.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Delete user account", user_id=current_user.user_id)

        deleted_user_lock = models.UserLock(user_lock_type="delete", user=current_user)
        db.session.add(deleted_user_lock)
        db.session.commit()

        log.info("User account deleted", user_id=current_user.user_id)

        return {"status": "Success", "username": [current_user.username]}

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
            confirm_new_password=new_password,
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

        stmt = select(models.User).filter_by(username=username)
        user: models.User | None = db.session.scalars(stmt).first()

        if not user.is_active:
            user = None

        if user is None:
            if error_if_not_found:
                log.error("User not found", username=username)
                raise UserDoesNotExistError

            return None

        return user

    def change_password(
        self,
        username: str,
        current_password: str,
        new_password: str,
        confirm_new_password: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Change a user's password.

        Args:
            username: The username of the user.
            current_password: The user's current password.
            new_password: The user's new password, to replace the current one after
                authentication.

        Returns:
            A dictionary containing the password change success message if the password
            change is successful.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Change a user's password", username=username)
        user = cast(
            models.User, self.get(username=username, error_if_not_found=True, log=log)
        )
        return self._user_password_service.change(
            user=user,
            current_password=current_password,
            new_password=new_password,
            log=log,
        )


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

        stmt = select(models.User).filter_by(user_id=user_id)
        user: models.User | None = db.session.scalars(stmt).first()

        if not user.is_active:
            user = None

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
            confirm_new_password=new_password,
            log=log,
        )


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
        self, user: models.User, current_password: str, new_password: str, **kwargs
    ) -> dict[str, Any]:
        """Change a user's password.

        Args:
            user: The user object.
            current_password: The user's current password.
            new_password: The user's new password, to replace the current one after
                authentication.

        Returns:
            A dictionary containing the password change success message if the password
            change is successful.

        Raises:
            UserPasswordChangeError: If the password change fails.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if not self._password_service.verify(
            password=current_password, hashed_password=user.password, log=log
        ):
            raise UserPasswordChangeError

        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        user.password = self._password_service.hash(password=new_password, log=log)
        user.alternative_id = uuid.uuid4()
        user.last_modified_on = timestamp
        user.password_expire_on = timestamp + datetime.timedelta(
            tz=datetime.timezone.utc, days=DAYS_TO_EXPIRE_PASSWORD_DEFAULT
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
        return pbkdf2_sha256.hash(password)

    def verify(self, password: str, hashed_password: str, **kwargs) -> bool:
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Verifying password")
        return pbkdf2_sha256.verify(password, hashed_password)


def build_user_ref(user: models.User) -> dict[str:Any]:
    return {"id": user.id, "username": user.username, "url": f"/users/{user.id}"}


def build_user(user: models.User) -> dict[str:Any]:
    return {
        "id": user.user_id,
        "username": user.username,
        "email": user.email_address,
    }


def build_current_user(user: models.User) -> dict[str:Any]:
    return {
        "id": user.user_id,
        "username": user.username,
        "email": user.email_address,
        "groups": [],  # [GroupMemberRefSchema.from_orm(g) for g in user.member_of]
        "createdOn": user.created_on,
        "lastModifiedOn": user.last_modified_on,
        "lastLoginOn": user.last_login_on,
        "passwordExpiresOn": user.password_expire_on,
    }


def build_paging_envelope(name, data, query, index, length):
    has_prev = index > 0
    has_next = len(data) > length
    is_complete = not (has_prev or has_next)
    data = data[:length]
    paged_data = {
        "query": query,
        "index": index,
        "is_complete": is_complete,
        "data": data,
    }
    if has_prev:
        prev_index = max(index - length, 0)
        prev_url = build_paging_url("users", query, prev_index, length)
        paged_data.update({"prev": prev_url})

    if has_next:
        next_index = index + length
        next_url = build_paging_url("users", query, next_index, length)
        paged_data.update({"next": next_url})

    return paged_data


def build_paging_url(name: str, search: str, index: int, length: int):
    return f"/{name}/?query={search}&index={index}&pageLength={length}"
