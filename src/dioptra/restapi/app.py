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
"""The top-level module of the Flask application.

:py:func:`~.create_app` is a factory function that instantiates a new
:py:class:`~flask.Flask` object and wires up all the configurations and third-party
dependencies.
"""
from __future__ import annotations

import os
import uuid
from typing import Any, Callable, List, Optional

import structlog
from flask import Flask, jsonify
from flask_cors import CORS
from flask_injector import FlaskInjector
from flask_migrate import Migrate
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from sqlalchemy import MetaData
from structlog.stdlib import BoundLogger

from .__version__ import __version__ as API_VERSION

LOGGER: BoundLogger = structlog.stdlib.get_logger()

cors: CORS = CORS()
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
        env = os.getenv("DIOPTRA_RESTAPI_ENV", "test")

    app: Flask = Flask(__name__)
    app.config.from_object(config_by_name[env])

    api: Api = Api(
        app,
        title="Dioptra REST API",
        version=API_VERSION,
        doc=app.config["DIOPTRA_SWAGGER_PATH"],
        url_scheme=app.config["DIOPTRA_BASE_URL"],
    )
    modules: List[Callable[..., Any]] = [bind_dependencies]

    register_routes(api, app)
    register_error_handlers(api)
    register_providers(modules)
    csrf.init_app(app)
    db.init_app(app)

    if env != "prod":
        cors.init_app(
            app, resources={r"/api/*": {"origins": app.config["DIOPTRA_CORS_ORIGIN"]}}
        )

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
