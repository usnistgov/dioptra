# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""The top-level module of the Flask application.

:py:func:`~.create_app` is a factory function that instantiates a new
:py:class:`~flask.Flask` object and wires up all the configurations and third-party
dependencies.
"""

import uuid
from typing import Any, Callable, List, Optional

import structlog
from flask import Flask, jsonify
from flask_injector import FlaskInjector
from flask_migrate import Migrate
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from sqlalchemy import MetaData
from structlog.stdlib import BoundLogger

from .__version__ import __version__ as API_VERSION

LOGGER: BoundLogger = structlog.stdlib.get_logger()

csrf: CSRFProtect = CSRFProtect()
db: SQLAlchemy = SQLAlchemy(
    metadata=MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(column_0_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )
)
migrate: Migrate = Migrate()


def create_app(env: Optional[str] = None, inject_dependencies: bool = True):
    """Creates and configures a fresh instance of the Dioptra REST API.

    Args:
        env: The configuration environment to use for the application. The allowed
            values are `"dev"`, `"prod"` and `"test"`. If `None`, the `"test"`
            configuration is used. The default is `None`.
        inject_dependencies: Controls whether or not the dependency injection settings
            in the ``dependencies.py`` files will be used. If `False`, then dependency
            injection is not used and the configuration of the shared services must be
            handled after the :py:class:`~flask.Flask` object is created. This is mostly
            useful when performing unit tests. The default is `True`.

    Returns:
        An initialized and configured :py:class:`~flask.Flask` object.
    """
    from .config import config_by_name
    from .dependencies import bind_dependencies, register_providers
    from .errors import register_error_handlers
    from .routes import register_routes

    if env is None:
        env = "test"

    app: Flask = Flask(__name__)
    app.config.from_object(config_by_name[env])

    api: Api = Api(
        app,
        title="Dioptra REST API",
        version=API_VERSION,
    )
    modules: List[Callable[..., Any]] = [bind_dependencies]

    register_routes(api, app)
    register_error_handlers(api)
    register_providers(modules)
    csrf.init_app(app)
    db.init_app(app)

    with app.app_context():
        migrate.init_app(app, db, render_as_batch=True)

    @app.route("/health")
    def health():
        """An endpoint for monitoring if the REST API is responding to requests."""
        log = LOGGER.new(request_id=str(uuid.uuid4()))  # noqa: F841
        return jsonify("healthy")

    if not inject_dependencies:
        return app

    FlaskInjector(app=app, modules=modules)

    return app
