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
"""The server-side functions that perform auth endpoint operations."""
from __future__ import annotations

import base64
import datetime
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Final, cast

import structlog
from flask_login import current_user, login_user, logout_user
from injector import inject
from joserfc import jwk
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.v1.users.service import UserNameService, UserPasswordService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

KEY_TYPE_TO_ALGORITHM_MAPPINGS: Final[dict[str, str]] = {
    "RSA": "RS256",
    "EC": "ES256",
    "OKP": "ES256",
}


@dataclass
class AsymmetricKey(object):
    key: jwk.RSAKey | jwk.ECKey | jwk.OKPKey

    @property
    def key_type(self) -> str:
        return self.key.key_type

    @classmethod
    def from_ascii(cls, data: str, key_type: str) -> "AsymmetricKey":
        key = jwk.JWKRegistry.import_key(
            base64.urlsafe_b64decode(data), key_type=key_type
        )
        cls._validate_key_type(key)
        return cls(key=cast(jwk.RSAKey | jwk.ECKey | jwk.OKPKey, key))

    @classmethod
    def from_dict(cls, data: dict[str, str | list[str]]) -> "AsymmetricKey":
        key = jwk.JWKRegistry.import_key(data)
        cls._validate_key_type(key)
        return cls(key=cast(jwk.RSAKey | jwk.ECKey | jwk.OKPKey, key))

    def to_ascii(self, private: bool = False) -> str:
        return base64.urlsafe_b64encode(self.key.as_der(private=private)).decode()

    def to_dict(self, private: bool = False) -> dict[str, str | list[str]]:
        return self.key.as_dict(private=private)

    @staticmethod
    def _validate_key_type(key: jwk.Key) -> None:
        if not isinstance(key, (jwk.RSAKey, jwk.ECKey, jwk.OKPKey)):
            raise ValueError(
                f"Received invalid key type {key.key_type}. Key must be based on an "
                "asymmetric algorithm. Current allowed algorithms are 'RSA', 'EC', "
                "and 'OKP'."
            )


@dataclass
class JwkSettings(object):
    key_type: str
    crv_or_size: str | int


class JwkService(object):
    def __init__(self, settings: JwkSettings) -> None:
        self._settings = settings

    def generate_asymmetric_key(self, **kwargs) -> AsymmetricKey:
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Generating asymmetric key", **asdict(self._settings))
        key = jwk.JWKRegistry.generate_key(**asdict(self._settings))
        return AsymmetricKey(key=cast(jwk.RSAKey | jwk.ECKey | jwk.OKPKey, key))

    def import_asymmetric_key(
        self, data: str | dict[str, str | list[str]], **kwargs
    ) -> AsymmetricKey:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if not isinstance(data, (str, dict)):
            data_type = type(data)
            log.error(
                "Invalid data type for importing asymmetric key", data_type=data_type
            )
            raise ValueError(
                f"Invalid data type {data_type} for importing asymmetric key"
            )

        if isinstance(data, dict):
            log.debug("Importing asymmetric key from dict")
            return AsymmetricKey.from_dict(data)

        if isinstance(data, str):
            log.debug(
                "Importing asymmetric key from ascii",
                key_type=self._settings.key_type,
            )
            return AsymmetricKey.from_ascii(data, key_type=self._settings.key_type)


class AuthService(object):
    """The service methods for user logins and logouts."""

    @inject
    def __init__(
        self,
        user_name_service: UserNameService,
        user_password_service: UserPasswordService,
    ) -> None:
        """Initialize the authentication service.

        All arguments are provided via dependency injection.

        Args:
            user_name_service: A UserNameService object.
            user_password_service: A UserPasswordService object.
        """
        self._user_name_service = user_name_service
        self._user_password_service = user_password_service

    def login(
        self,
        username: str,
        password: str,
        **kwargs,
    ) -> dict[str, Any]:
        """Login the user with the given username and password.

        Args:
            username: The username for logging into the user account.
            password: The password for authenticating the user account.

        Returns:
            A dictionary containing the login success message.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        user = cast(
            models.User,
            self._user_name_service.get(
                username=username, error_if_not_found=True, log=log
            ),
        )
        self._user_password_service.authenticate(
            password=password,
            user_password=str(user.password),
            expiration_date=user.password_expire_on,
            error_if_failed=True,
            log=log,
        )
        login_user(user, remember=True)
        user.last_login_on = datetime.datetime.now(tz=datetime.timezone.utc)
        db.session.commit()
        log.debug("Login successful", user_id=user.user_id)
        return {"status": "Login successful", "username": username}

    def logout(self, everywhere: bool, **kwargs) -> dict[str, Any]:
        """Log the current user out.

        Args:
            everywhere: If True, log out from all devices by regenerating the current
                user's alternative id.

        Returns:
            A dictionary containing the logout success message.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        user_id = current_user.user_id
        username = current_user.username

        if everywhere:
            current_user.alternative_id = uuid.uuid4()
            db.session.commit()

        logout_user()
        log.debug("Logout successful", user_id=user_id, everywhere=everywhere)
        return {
            "status": "Logout successful",
            "username": username,
            "everywhere": everywhere,
        }
