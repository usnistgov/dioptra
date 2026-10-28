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
"""Resolve and validate settings for one explicitly selected API mode.

Class attributes are packaged defaults. Use ``load_config`` to obtain a fresh
instance; importing this module never reads deployment settings or key files.
"""

import logging
import os
from collections.abc import Iterable, Mapping
from pathlib import Path

from marshmallow import Schema, ValidationError, fields, validate
from redis.connection import parse_url as parse_redis_url
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from .key_file import _is_windows, _resolve_key_file, _validate_key_content, read_key


class _Boolean(fields.Boolean):
    """Accept only Python booleans during schema validation."""

    def _deserialize(self, value, attr, data, **kwargs):
        if type(value) is not bool:
            raise ValidationError("Use a Python boolean.")
        return value


class _String(fields.String):
    """Accept only Python strings during schema validation."""

    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, str):
            raise ValidationError("Use a Python string.")
        return value


def _database_uri(value: str) -> None:
    """Reject values that SQLAlchemy cannot parse as database URIs."""
    try:
        make_url(value)
    except (ArgumentError, ValueError, TypeError):
        raise ValidationError("Use a valid SQLAlchemy database URI.") from None


def _redis_uri(value: str) -> None:
    """Reject values that Redis cannot parse as supported connection URIs."""
    try:
        parse_redis_url(value)
    except (ValueError, TypeError):
        raise ValidationError(
            "Use a valid redis://, rediss:// or unix:// URI."
        ) from None


def _swagger_path(value: object) -> None:
    """Reject values other than strings or False for the documentation path."""
    if not isinstance(value, str) and value is not False:
        raise ValidationError("Use a string or False to disable documentation.")


class _ConfigSchema(Schema):
    """Validate the resolved application settings and their constraints."""

    DEBUG = _Boolean(required=True)
    TESTING = _Boolean(required=True)
    LOGIN_DISABLED = _Boolean(required=True)
    REMEMBER_COOKIE_SECURE = _Boolean(required=True)
    SQLALCHEMY_TRACK_MODIFICATIONS = _Boolean(required=True)
    USE_MOCK_EQUIVALENCY = _Boolean(required=True)
    SESSION_PROTECTION = _String(
        required=True, allow_none=True, validate=validate.OneOf(["basic", "strong"])
    )
    REMEMBER_COOKIE_NAME = _String(required=True, validate=validate.Length(min=1))
    REMEMBER_COOKIE_DURATION = fields.Integer(required=True, strict=True)
    DIOPTRA_CORS_ORIGIN = _String(required=True, validate=validate.Length(min=1))
    # Flask-RESTX accepts False to disable its documentation endpoint.
    DIOPTRA_SWAGGER_PATH = fields.Raw(required=True, validate=_swagger_path)
    DIOPTRA_BASE_URL = _String(
        required=True, allow_none=True, validate=validate.Length(min=1)
    )
    DIOPTRA_MAX_PAGE_SIZE = fields.Integer(
        required=True, strict=True, validate=validate.Range(min=10)
    )
    SQLALCHEMY_DATABASE_URI = _String(
        required=True, validate=[validate.Length(min=1), _database_uri]
    )
    RQ_REDIS_URI = _String(required=True, validate=[validate.Length(min=1), _redis_uri])
    MLFLOW_TRACKING_URI = _String(required=True, validate=validate.Length(min=1))
    DIOPTRA_RESTAPI_LOG_AS_JSON = _Boolean(required=True)
    DIOPTRA_RESTAPI_LOG_LEVEL = _String(
        required=True, validate=validate.OneOf(list(logging.getLevelNamesMapping()))
    )


class BaseConfig:
    """Hold settings resolved by ``load_config`` for one application.

    Do not construct instances directly or mutate them after resolution. Pass a
    resolved instance to ``create_app(settings=...)`` without other settings inputs.
    """

    CONFIG_NAME = "base"
    SECRET_KEY: str | None = None
    SECRET_KEY_FILE: Path | None = None
    USE_MOCK_EQUIVALENCY = False
    DEBUG = False
    TESTING = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI: str | None = None
    REMEMBER_COOKIE_NAME = "dioptra_remember_token"
    REMEMBER_COOKIE_DURATION = 1209600
    REMEMBER_COOKIE_SECURE = False
    LOGIN_DISABLED = False
    SESSION_PROTECTION: str | None = "strong"
    DIOPTRA_CORS_ORIGIN = "http://localhost:5173"
    DIOPTRA_SWAGGER_PATH: str | bool = "/"
    DIOPTRA_BASE_URL: str | None = None
    DIOPTRA_MAX_PAGE_SIZE = 1000
    RQ_REDIS_URI = "redis://"
    MLFLOW_TRACKING_URI: str | None = None
    DIOPTRA_RESTAPI_LOG_AS_JSON = False
    DIOPTRA_RESTAPI_LOG_LEVEL = "INFO"
    _resolved = False

    def validate(self) -> None:
        """Reject incomplete settings or values that violate operating policy.

        Validation uses this instance alone, without environment resolution or
        filesystem/service access. Invalid settings raise ``ValueError`` with
        setting names rather than credential values.
        """
        if not self._resolved:
            raise ValueError("Create resolved settings with load_config().")
        _check_mode(self.CONFIG_NAME)
        if type(self) is not config_by_name[self.CONFIG_NAME]:
            raise ValueError("CONFIG_NAME must match the resolved configuration class.")
        _validate_values(self)
        if self.CONFIG_NAME == "prod":
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production.")
            if self.LOGIN_DISABLED:
                raise ValueError("LOGIN_DISABLED must be False in production.")
        path = self.SECRET_KEY_FILE
        if not isinstance(path, Path) or not path.is_absolute():
            raise ValueError("SECRET_KEY_FILE must be a resolved absolute path.")
        if not isinstance(self.SECRET_KEY, str) or len(self.SECRET_KEY) != 64:
            raise ValueError("SECRET_KEY must be read from SECRET_KEY_FILE.")
        try:
            _validate_key_content(self.SECRET_KEY.encode("ascii"), path)
        except UnicodeError:
            raise ValueError(
                "SECRET_KEY must contain the protected file's key."
            ) from None


class DevelopmentConfig(BaseConfig):
    """Packaged defaults for explicit development mode."""

    CONFIG_NAME = "dev"
    DEBUG = True


class ProductionConfig(BaseConfig):
    """Packaged defaults for explicit production mode."""

    CONFIG_NAME = "prod"


config_by_name = {"dev": DevelopmentConfig, "prod": ProductionConfig}

# Only current environment inputs belong here. Other Flask attributes can be
# overridden explicitly, while SECRET_KEY and CONFIG_NAME have dedicated sources.
_ENVIRONMENT_SETTINGS = {
    "LOGIN_DISABLED": "DIOPTRA_LOGIN_DISABLED",
    "SESSION_PROTECTION": "DIOPTRA_SESSION_PROTECTION",
    "REMEMBER_COOKIE_DURATION": "DIOPTRA_REMEMBER_COOKIE_DURATION",
    "REMEMBER_COOKIE_SECURE": "DIOPTRA_REMEMBER_COOKIE_SECURE",
    "DIOPTRA_CORS_ORIGIN": "DIOPTRA_CORS_ORIGIN",
    "DIOPTRA_SWAGGER_PATH": "DIOPTRA_SWAGGER_PATH",
    "DIOPTRA_BASE_URL": "DIOPTRA_BASE_URL",
    "DIOPTRA_MAX_PAGE_SIZE": "DIOPTRA_MAX_PAGE_SIZE",
    "RQ_REDIS_URI": "RQ_REDIS_URI",
    "MLFLOW_TRACKING_URI": "MLFLOW_TRACKING_URI",
    "DIOPTRA_RESTAPI_LOG_AS_JSON": "DIOPTRA_RESTAPI_LOG_AS_JSON",
    "DIOPTRA_RESTAPI_LOG_LEVEL": "DIOPTRA_RESTAPI_LOG_LEVEL",
}
_BOOLEAN_ENVIRONMENT_SETTINGS = {
    "LOGIN_DISABLED",
    "REMEMBER_COOKIE_SECURE",
    "DIOPTRA_RESTAPI_LOG_AS_JSON",
}
_INTEGER_ENVIRONMENT_SETTINGS = {"REMEMBER_COOKIE_DURATION", "DIOPTRA_MAX_PAGE_SIZE"}


def _check_mode(mode: str | None) -> str:
    """Validate the mode and reject production on native Windows."""
    if not isinstance(mode, str) or mode not in config_by_name:
        raise ValueError(
            "DIOPTRA_RESTAPI_ENV requires an explicit 'dev' or 'prod' mode."
        )
    if _is_windows() and mode == "prod":
        raise ValueError(
            "Production is unsupported on native Windows; use a POSIX host."
        )
    return mode


def _resolve_mode(env: str | None, environment: Mapping[str, str]) -> str:
    """Select the explicit mode or the environment value, then validate it."""
    return _check_mode(
        env if env is not None else environment.get("DIOPTRA_RESTAPI_ENV")
    )


def resolve_mode(env: str | None = None) -> str:
    """Select and validate the API operating mode.

    Args:
        env: ``dev`` or ``prod``. If omitted, use ``DIOPTRA_RESTAPI_ENV``.

    Returns:
        The selected mode. Debug and testing flags do not select it.

    Raises:
        ValueError: If the mode is missing or unsupported, or production is
            selected on native Windows.
    """
    return _resolve_mode(env, dict(os.environ))


def _resolve_database_uri(
    environment: Mapping[str, str], overrides: Mapping[str, object]
) -> str:
    """Resolve and validate the database URI from a supplied environment snapshot.

    An explicit override takes precedence; absent both sources, use an absolute
    SQLite path in the current directory. Reject the retired development variable
    even when another URI is supplied.
    """
    if "DIOPTRA_RESTAPI_DEV_DATABASE_URI" in environment:
        raise ValueError(
            "Remove retired DIOPTRA_RESTAPI_DEV_DATABASE_URI; "
            "use DIOPTRA_RESTAPI_DATABASE_URI instead."
        )
    uri = overrides.get(
        "SQLALCHEMY_DATABASE_URI", environment.get("DIOPTRA_RESTAPI_DATABASE_URI")
    )
    if uri is None and "SQLALCHEMY_DATABASE_URI" not in overrides:
        uri = f"sqlite:///{Path.cwd() / 'dioptra.db'}"
    if not isinstance(uri, str):
        raise ValueError("SQLALCHEMY_DATABASE_URI requires a valid database URI.")
    try:
        _ConfigSchema(only=["SQLALCHEMY_DATABASE_URI"]).load(
            {"SQLALCHEMY_DATABASE_URI": uri}
        )
    except ValidationError:
        raise ValueError(
            "SQLALCHEMY_DATABASE_URI requires a valid database URI."
        ) from None
    return uri


def resolve_database_uri(*, overrides: Mapping[str, object] | None = None) -> str:
    """Resolve the common database URI without an API mode or signing key.

    Args:
        overrides: Optional mapping containing only ``SQLALCHEMY_DATABASE_URI``.
            Its value takes precedence over ``DIOPTRA_RESTAPI_DATABASE_URI``.

    Returns:
        The selected SQLAlchemy URI. With neither source, this is an absolute
        SQLite URI for ``dioptra.db`` in the current directory.

    Raises:
        ValueError: If the URI is invalid, an override is unsupported, or the
            retired development database URI variable is present.
    """
    supplied = {} if overrides is None else overrides
    _check_overrides(supplied, {"SQLALCHEMY_DATABASE_URI"})
    return _resolve_database_uri(dict(os.environ), supplied)


def _check_overrides(overrides: Mapping[str, object], allowed: set[str]) -> None:
    for name in overrides:
        if name not in allowed:
            raise ValueError(f"Unsupported configuration setting: {name}.")


def _parse_environment_value(name: str, value: str) -> object:
    """Convert named boolean and integer settings from their environment strings."""
    if name in _BOOLEAN_ENVIRONMENT_SETTINGS:
        values = {"true": True, "1": True, "false": False, "0": False}
        try:
            return values[value.strip().lower()]
        except KeyError:
            raise ValueError(f"{name} requires true, false, 1 or 0.") from None
    if name in _INTEGER_ENVIRONMENT_SETTINGS:
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"{name} requires an integer.") from None
    return value


def _validate_values(settings: BaseConfig) -> None:
    """Validate schema fields and report invalid names without their values."""
    schema = _ConfigSchema()
    try:
        schema.load({name: getattr(settings, name) for name in schema.fields})
    except ValidationError as error:
        names = ", ".join(sorted(error.messages))
        raise ValueError(
            f"Invalid configuration for {names}; check types and constraints."
        ) from None


def _populate_settings(
    settings: BaseConfig,
    names: Iterable[str],
    environment: Mapping[str, str],
    overrides: Mapping[str, object],
) -> None:
    """Populate named fields from overrides, the snapshot, then class defaults.

    Convert only environment inputs. Typed overrides remain unchanged so later
    schema validation can reject invalid caller values. Mutate the supplied
    settings without reading the process environment or validating the fields.
    """
    for name in names:
        variable = _ENVIRONMENT_SETTINGS.get(name)
        if name in overrides:
            value = overrides[name]
        elif variable is not None and variable in environment:
            value = _parse_environment_value(name, environment[variable])
        else:
            value = getattr(settings, name)
        setattr(settings, name, value)


def load_config(
    env: str | None = None, *, overrides: Mapping[str, object] | None = None
) -> BaseConfig:
    """Resolve a fresh API configuration from one environment snapshot.

    Explicit typed overrides precede named environment inputs and class defaults.
    The protected key file must already exist; resolution never creates or repairs
    it. The returned instance belongs to one application and must not be mutated.
    It contains the signing key, so do not print or serialize it. Later environment
    changes affect future resolution, not applications using this instance.
    ``DIOPTRA_MAX_PAGE_SIZE`` applies to paginated endpoints and must be at
    least 10. Session protection accepts ``basic``, ``strong`` or None; the
    environment string ``none`` selects None.

    Args:
        env: ``dev`` or ``prod``. If omitted, select ``DIOPTRA_RESTAPI_ENV``.
        overrides: Mapping of schema setting names to typed values, plus the optional
            ``SECRET_KEY_FILE`` path. Unsupported names are rejected. See the schema
            and class defaults for the accepted settings.

    Returns:
        A validated development or production configuration, including the key
        read from the selected file and the resolved database and service URIs.

    Raises:
        ValueError: If mode, settings, retired environment inputs, or the selected
            key file fail validation. Diagnostics do not include credential values.
    """
    environment = dict(os.environ)
    mode = _resolve_mode(env, environment)
    supplied = {} if overrides is None else overrides
    schema = _ConfigSchema()
    _check_overrides(supplied, set(schema.fields) | {"SECRET_KEY_FILE"})
    if "DIOPTRA_DEPLOY_SECRET_KEY" in environment:
        raise ValueError(
            "Remove retired DIOPTRA_DEPLOY_SECRET_KEY; initialize a protected key "
            "file and set DIOPTRA_RESTAPI_SECRET_KEY_FILE instead."
        )
    settings = config_by_name[mode]()
    _populate_settings(settings, schema.fields, environment, supplied)
    settings.SQLALCHEMY_DATABASE_URI = _resolve_database_uri(environment, supplied)
    if settings.MLFLOW_TRACKING_URI is None and "MLFLOW_TRACKING_URI" not in supplied:
        import mlflow

        settings.MLFLOW_TRACKING_URI = mlflow.get_tracking_uri()
    if isinstance(settings.SESSION_PROTECTION, str):
        protection = settings.SESSION_PROTECTION.lower()
        settings.SESSION_PROTECTION = None if protection == "none" else protection
    if isinstance(settings.DIOPTRA_RESTAPI_LOG_LEVEL, str):
        settings.DIOPTRA_RESTAPI_LOG_LEVEL = settings.DIOPTRA_RESTAPI_LOG_LEVEL.upper()
    # Validate ordinary values before opening the selected key or constructing clients.
    _validate_values(settings)
    if mode == "prod" and (settings.DEBUG or settings.LOGIN_DISABLED):
        raise ValueError("Production requires DEBUG=False and LOGIN_DISABLED=False.")
    if "SECRET_KEY_FILE" in supplied and supplied["SECRET_KEY_FILE"] is None:
        raise ValueError("SECRET_KEY_FILE requires a nonempty filesystem path.")
    settings.SECRET_KEY_FILE = _resolve_key_file(
        supplied.get("SECRET_KEY_FILE"), environment
    )
    settings.SECRET_KEY = read_key(settings.SECRET_KEY_FILE, development=mode == "dev")
    settings._resolved = True
    settings.validate()
    return settings
