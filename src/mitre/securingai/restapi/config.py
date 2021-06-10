# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""A module for the Flask configuration environments.

There are three configuration environments available,

- **dev:** The configuration for interactive development sessions.
- **prod:** The configuration for production environments.
- **test:** The configuration for running unit tests.
"""

import os
from typing import List, Type


class BaseConfig(object):
    CONFIG_NAME = "base"
    USE_MOCK_EQUIVALENCY = False
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    AI_PLUGINS_BUCKET = os.getenv("AI_PLUGINS_BUCKET", "plugins")


class DevelopmentConfig(BaseConfig):
    CONFIG_NAME = "dev"
    SECRET_KEY = os.getenv("AI_DEPLOY_SECRET_KEY", "deploy123")
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "AI_RESTAPI_DEV_DATABASE_URI",
        f"sqlite:///{os.path.join(os.getcwd(), 'securingai-dev.db')}",
    )


class TestingConfig(BaseConfig):
    CONFIG_NAME = "test"
    SECRET_KEY = os.getenv("AI_DEPLOY_SECRET_KEY", "deploy123")
    DEBUG = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.getenv("AI_RESTAPI_TEST_DATABASE_URI", "sqlite://")


class ProductionConfig(BaseConfig):
    CONFIG_NAME = "prod"
    SECRET_KEY = os.getenv("AI_DEPLOY_SECRET_KEY", "deploy123")
    DEBUG = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "AI_RESTAPI_DATABASE_URI",
        f"sqlite:///{os.path.join(os.getcwd(), 'securingai.db')}",
    )


EXPORT_CONFIGS: List[Type[BaseConfig]] = [
    DevelopmentConfig,
    TestingConfig,
    ProductionConfig,
]
config_by_name = {cfg.CONFIG_NAME: cfg for cfg in EXPORT_CONFIGS}
