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
from sqlalchemy import func, select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.db.models.constants import user_lock_types
from dioptra.restapi.errors import BackendDatabaseError
from dioptra.restapi.v1.groups.service import GroupMemberService, GroupNameService
from dioptra.restapi.v1.plugin_parameter_types.service import (
    BuiltinPluginParameterTypeService,
)
from dioptra.restapi.v1.shared.password_service import PasswordService
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters

from .errors import (
    NoCurrentUserError,
    UserDoesNotExistError,
    UserEmailNotAvailableError,
    UsernameNotAvailableError,
    UserPasswordChangeError,
    UserPasswordChangeSamePasswordError,
    UserPasswordExpiredError,
    UserPasswordVerificationError,
    UserRegistrationError,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

DEFAULT_GROUP_NAME: Final[str] = "public"
DEFAULT_GROUP_PERMISSIONS: Final[dict[str, Any]] = {
    "read": True,
    "write": True,
    "share_read": False,
    "share_write": False,
}
DAYS_TO_EXPIRE_PASSWORD_DEFAULT: Final[int] = 365
SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "username": lambda x: models.User.username.like(x, escape="/"),
    "email": lambda x: models.User.email_address.like(x, escape="/"),
}


class UserService(object):
    """The service methods used for creating and managing user accounts."""

    @inject
    def __init__(
        self,
        user_password_service: UserPasswordService,
        user_name_service: UserNameService,
        group_name_service: GroupNameService,
        group_member_service: GroupMemberService,
        builtin_plugin_parameter_type_service: BuiltinPluginParameterTypeService,
    ) -> None:
        """Initialize the user service.

        All arguments are provided via dependency injection.

        Args:
            user_password_service: A UserPasswordService object.
            user_name_service: A UserNameService object.
            group_name_service: A GroupNameService object.
            group_member_service: A GroupMemberService object.
            builtin_plugin_parameter_type_service: A BuiltinPluginParameterTypeService
                object.
        """
        self._user_password_service = user_password_service
        self._user_name_service = user_name_service
        self._group_name_service = group_name_service
        self._group_member_service = group_member_service
        self._builtin_plugin_parameter_type_service = (
            builtin_plugin_parameter_type_service
        )

    def create(
        self,
        username: str,
        email_address: str,
        password: str,
        confirm_password: str,
        commit: bool = True,
        **kwargs,
    ) -> models.User:
        """Create a new user.

        Args:
            username: The username requested by the new user. Must be unique.
            email_address: The email address to associate with the new user. Must be
                unique.
            password: The password for the new user.
            confirm_password: The password confirmation for the new user.
            commit: If True, commit the transaction. Defaults to True.

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
            log.debug("Username already exists", username=username)
            raise UsernameNotAvailableError

        if self._get_user_by_email(email_address, log=log) is not None:
            log.debug("Email already exists", email_address=email_address)
            raise UserEmailNotAvailableError

        hashed_password = self._user_password_service.hash(password, log=log)
        new_user: models.User = models.User(
            username=username, password=hashed_password, email_address=email_address
        )

        default_group = self._create_or_get_default_group(
            user=new_user,
            log=log,
        )
        self._group_member_service.create(
            default_group,
            user=new_user,
            permissions=DEFAULT_GROUP_PERMISSIONS,
            commit=False,
            log=log,
        )

        db.session.add(new_user)
        db.session.add(default_group)

        if commit:
            db.session.commit()
            log.debug("User registration successful", user_id=new_user.user_id)

        return new_user

    def get(
        self,
        search_string: str,
        page_index: int,
        page_length: int,
        **kwargs,
    ) -> tuple[list[models.User], int]:
        """Fetch a list of users, optionally filtering by search string and paging
        parameters.

        Args:
            search_string: A search string used to filter results.
            page_index: The index of the first user to be returned.
            page_length: The maximum number of users to be returned.

        Returns:
            A tuple containing a list of users and the total number of users matching
            the query.

        Raises:
            BackendDatabaseError: If the database query returns a None when counting
                the number of users.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get list of users")

        search_filters = construct_sql_query_filters(search_string, SEARCHABLE_FIELDS)

        stmt = (
            select(func.count(models.User.user_id))
            .filter_by(is_deleted=False)
            .filter(search_filters)
        )
        total_num_users = db.session.scalars(stmt).first()

        if total_num_users is None:
            log.error(
                "The database query returned a None when counting the number of "
                "users when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        if total_num_users == 0:
            return cast(list[models.User], []), total_num_users

        stmt = (
            select(models.User)  # type: ignore
            .filter_by(is_deleted=False)
            .filter(search_filters)
            .offset(page_index)
            .limit(page_length)
        )
        users = cast(list[models.User], db.session.scalars(stmt).all())

        return users, total_num_users

    def _get_user_by_email(
        self, email_address: str, error_if_not_found: bool = False, **kwargs
    ) -> models.User | None:
        """Lookup a user by email address.

        Args:
            email_address: The email address of the user.
            error_if_not_found: If True, raise an error if the user is not found.
                Defaults to False.

        Returns:
            The user object if found, otherwise None.

        Raises:
            UserDoesNotExistError: If the user is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Lookup user account by email", email_address=email_address)

        stmt = select(models.User).filter_by(
            email_address=email_address, is_deleted=False
        )
        user: models.User | None = db.session.scalars(stmt).first()

        if user is None:
            if error_if_not_found:
                log.debug("User not found", email_address=email_address)
                raise UserDoesNotExistError

            return None

        return user

    def _create_or_get_default_group(
        self,
        user: models.User,
        **kwargs,
    ) -> models.Group:
        """Returns the default group if it exists, otherwise create and return it.

        Args:
            user: The user to assign as the creator of the group. If group already
                exists, then this does nothing.

        Returns:
            The group object if found, otherwise None.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if (
            group := self._group_name_service.get(DEFAULT_GROUP_NAME, log=log)
        ) is not None:
            return group

        default_group = models.Group(name=DEFAULT_GROUP_NAME, creator=user)
        # Register the built-in plugin parameter types when creating a new group.
        self._builtin_plugin_parameter_type_service.create_all(
            user=user, group=default_group, commit=False
        )
        return default_group


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
        log.debug("Lookup user account by unique id", user_id=user_id)

        stmt = select(models.User).filter_by(user_id=user_id, is_deleted=False)
        user = db.session.scalars(stmt).first()

        if user is None:
            if error_if_not_found:
                log.debug("User not found", user_id=user_id)
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
        """Change a user's password.

        Args:
            user_id: The user's unique id.
            current_password: The user's current password.
            new_password: The user's new password, to replace the current one after
                authentication.
            confirm_new_password: Confirmation of the new password.

        Returns:
            A dictionary containing the password change success message if the password
            change is successful.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Change a user's password by ID.", user_id=user_id)
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
            log.debug("There is no current user.")
            raise NoCurrentUserError

        return cast(models.User, current_user)

    def modify(
        self, username: str, email_address: str, commit: bool = True, **kwargs
    ) -> models.User:
        """Modifies the current user

        Args:
            username: The user's current username.
            email_address: The user's current email_address.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The current user object.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Modify user account", user_id=current_user.user_id)

        current_timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        current_user.username = username
        current_user.email_address = email_address
        current_user.last_modified_on = current_timestamp

        if commit:
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
        log.debug("Delete user account", user_id=current_user.user_id)
        self._user_password_service.authenticate(
            password=password,
            user_password=current_user.password,
            expiration_date=current_user.password_expire_on,
            error_if_failed=True,
            log=log,
        )

        user_id = current_user.user_id
        username = current_user.username

        deleted_user_lock = models.UserLock(
            user_lock_type=user_lock_types.DELETE,
            user=current_user,
        )
        db.session.add(deleted_user_lock)
        db.session.commit()
        log.debug("User account deleted", user_id=user_id, username=username)

        return {"status": "Success", "id": [user_id]}

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
        log.debug("Change the current user's password", user_id=current_user.user_id)
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
        log.debug("Lookup user account by unique username", username=username)

        stmt = select(models.User).filter_by(username=username, is_deleted=False)
        user = db.session.scalars(stmt).first()

        if user is None:
            if error_if_not_found:
                log.debug("User not found", username=username)
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
            log.debug("Password authentication failed.")
            raise UserPasswordVerificationError

        if expiration_date < current_timestamp:
            log.debug("Password expired")
            raise UserPasswordExpiredError

        return authenticated

    def change(
        self,
        user: models.User,
        current_password: str,
        new_password: str,
        confirm_new_password: str,
        commit: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """Change a user's password.

        Args:
            user: The user object.
            current_password: The user's current password.
            new_password: The user's new password, to replace the current one after
                authentication.
            confirm_new_password: Confirmation of the new password.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            A dictionary containing the password change success message if the password
            change is successful.

        Raises:
            UserPasswordChangeError: If the password change fails.
            UserPasswordChangeSamePasswordError: If the new password is the same as the
                current password.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if not self._password_service.verify(
            password=current_password, hashed_password=str(user.password), log=log
        ):
            raise UserPasswordChangeError

        if new_password != confirm_new_password:
            raise UserPasswordChangeError

        if self._password_service.verify(
            password=new_password, hashed_password=str(user.password), log=log
        ):
            raise UserPasswordChangeSamePasswordError

        timestamp = datetime.datetime.now(tz=datetime.timezone.utc)
        user.password = self._password_service.hash(password=new_password, log=log)
        user.alternative_id = uuid.uuid4()
        user.last_modified_on = timestamp
        user.password_expire_on = timestamp + datetime.timedelta(
            days=DAYS_TO_EXPIRE_PASSWORD_DEFAULT
        )

        if commit:
            db.session.commit()

        return {"status": "Password Change Success", "username": user.username}

    def hash(self, password: str, **kwargs) -> str:
        """Hash a password.

        Args:
            password: The password to hash.

        Returns:
            The hashed password.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        return self._password_service.hash(password=password, log=log)


def load_user(user_id: str) -> models.User | None:
    """Load the user associated with a provided id.

    This function is intended for use with Flask-Login. The use of the alternative ID is
    needed to support the "logout everywhere" functionality and provides a mechanism for
    expiring sessions.


    Args:
        user_id: A string containing a UUID that matches the user's alternative ID.

    Returns:
        A user object if the user is found, otherwise None.
    """
    stmt = select(models.User).filter_by(
        alternative_id=uuid.UUID(user_id), is_deleted=False
    )
    return db.session.scalars(stmt).first()
