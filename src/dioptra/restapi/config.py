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
"""A module for the Flask configuration environments.

There are three configuration environments available,

- **dev:** The configuration for interactive development sessions.
- **prod:** The configuration for production environments.
- **test:** The configuration for running unit tests.
"""

import os
from typing import List, Type


def _set_session_protection(default: str = "strong") -> str:
    """Set the session protection level.

    The session protection level is set by the environment variable
    DIOPTRA_SESSION_PROTECTION. If the environment variable is not set, the default
    value is used.

    Args:
        default: The default session protection level. Must be one of "none", "basic",
            or "strong". Defaults to "strong".

    Returns:
        The session protection level.
    """
    allowed = {"none", "basic", "strong"}
    value = os.getenv("DIOPTRA_SESSION_PROTECTION", default).lower()

    if value not in allowed:
        raise ValueError(
            f"Invalid DIOPTRA_SESSION_PROTECTION value: {value}. "
            f"Allowed values are {allowed}."
        )

    return value


def _set_max_page_size(default_max: int = 1000) -> int:
    """
    Find a max page size.  This determines the maximum size of pages which
    restapi users are allowed to request.  It applies across all endpoints
    which support paging.

    It can be set via environment variable DIOPTRA_MAX_PAGE_SIZE.  The given
    default is used if the variable is not set.  In all cases, the max page
    size can't be less than the default page size, which is currently 10.

    Args:
        default_max: The default value to use for max page size, if the
            environment variable is not set

    Returns:
        The max page size value

    Raises:
        ValueError: if the environment variable is set to a value which can't
            be converted to an integer, or is less than the default page size
    """
    # should match the marshmallow schema's load_default
    default_page_size = 10

    max_page_size = int(os.getenv("DIOPTRA_MAX_PAGE_SIZE", default_max))

    if max_page_size < default_page_size:
        raise ValueError(
            f"Invalid DIOPTRA_MAX_PAGE_SIZE value: {max_page_size}. "
            f"Must be >= {default_page_size}."
        )

    return max_page_size


class BaseConfig(object):
    CONFIG_NAME = "base"
    USE_MOCK_EQUIVALENCY = False
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_NAME = "dioptra_remember_token"
    REMEMBER_COOKIE_DURATION = int(
        os.getenv("DIOPTRA_REMEMBER_COOKIE_DURATION", f"{14 * 86400}")
    )
    REMEMBER_COOKIE_SECURE = os.getenv("DIOPTRA_REMEMBER_COOKIE_SECURE") is not None
    LOGIN_DISABLED = os.getenv("DIOPTRA_LOGIN_DISABLED") is not None
    DIOPTRA_CORS_ORIGIN = os.getenv("DIOPTRA_CORS_ORIGIN", "http://localhost:5173")
    DIOPTRA_PLUGINS_BUCKET = os.getenv("DIOPTRA_PLUGINS_BUCKET", "plugins")
    DIOPTRA_SWAGGER_PATH = os.getenv("DIOPTRA_SWAGGER_PATH", "/")
    DIOPTRA_BASE_URL = os.getenv("DIOPTRA_BASE_URL")
    DIOPTRA_MAX_PAGE_SIZE = _set_max_page_size()


class DevelopmentConfig(BaseConfig):
    CONFIG_NAME = "dev"
    SECRET_KEY = os.getenv("DIOPTRA_DEPLOY_SECRET_KEY", "deploy123")
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = False
    SESSION_PROTECTION = _set_session_protection()
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DIOPTRA_RESTAPI_DEV_DATABASE_URI",
        f"sqlite:///{os.path.join(os.getcwd(), 'dioptra-dev.db')}",
    )


class TestingConfig(BaseConfig):
    CONFIG_NAME = "test"
    SECRET_KEY = os.getenv("DIOPTRA_DEPLOY_SECRET_KEY", "deploy123")
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    SESSION_PROTECTION: str | None = None
    SQLALCHEMY_DATABASE_URI = "sqlite://"


class ProductionConfig(BaseConfig):
    CONFIG_NAME = "prod"
    SECRET_KEY = os.getenv("DIOPTRA_DEPLOY_SECRET_KEY", "deploy123")
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = False
    SESSION_PROTECTION = _set_session_protection()
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DIOPTRA_RESTAPI_DATABASE_URI",
        f"sqlite:///{os.path.join(os.getcwd(), 'dioptra.db')}",
    )


class TestingLoginDisabledConfig(TestingConfig):
    CONFIG_NAME = "test_no_login"
    LOGIN_DISABLED = True


class TestingV1Config(TestingConfig):
    CONFIG_NAME = "test_v1"


EXPORT_CONFIGS: List[Type[BaseConfig]] = [
    DevelopmentConfig,
    TestingConfig,
    ProductionConfig,
    TestingV1Config,
    TestingLoginDisabledConfig,
]
config_by_name = {cfg.CONFIG_NAME: cfg for cfg in EXPORT_CONFIGS}
