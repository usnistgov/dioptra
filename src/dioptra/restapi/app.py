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

import os
import uuid
from collections.abc import Mapping
from typing import Any, Callable, List

import structlog
from flask import Flask, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_restx import Api
from injector import Binder, Injector
from structlog.stdlib import BoundLogger

from dioptra.restapi.utils import setup_injection

from .__version__ import __version__ as DIOPTRA_VERSION
from .config import BaseConfig, load_config
from .db import db
from .patches import monkey_patch_flask_restx

LOGGER: BoundLogger = structlog.stdlib.get_logger()

cors: CORS = CORS()
login_manager = LoginManager()
migrate: Migrate = Migrate()


def create_app(
    env: str | None = None,
    injector: Injector | None = None,
    *,
    settings: BaseConfig | None = None,
    overrides: Mapping[str, object] | None = None,
) -> Flask:
    """Construct an API application after validating its settings.

    Supply a mode and optional overrides, or supply a previously resolved
    settings instance. The settings belong to this application and must not be
    mutated. They contain the signing key, so do not print or serialize them.
    Invalid or conflicting settings fail before extensions or default
    clients initialize. A supplied settings instance is validated; if the mode
    environment variable is present, it is ignored with a warning.

    Args:
        env: ``dev`` or ``prod``. When resolving settings, omission selects
            ``DIOPTRA_RESTAPI_ENV``. Do not supply this with ``settings``.
        injector: Injector used by RESTX views. If omitted, construct one with
            the default services. A supplied injector does not alter policy.
        settings: A configuration returned by ``load_config``. Do not combine
            it with ``env`` or ``overrides``.
        overrides: Typed values for settings accepted by ``load_config``. They
            precede named environment inputs and defaults. Do not supply these
            with ``settings``.

    Returns:
        An initialized and configured :py:class:`~flask.Flask` application.

    Raises:
        ValueError: If settings inputs conflict or configuration validation fails.
    """
    if settings is None:
        settings = load_config(env, overrides=overrides)
    else:
        if env is not None or overrides is not None:
            raise ValueError("Supply settings alone, without env or overrides.")
        settings.validate()
        if "DIOPTRA_RESTAPI_ENV" in os.environ:
            LOGGER.warning(
                "DIOPTRA_RESTAPI_ENV is ignored because resolved configuration was supplied",
                DIOPTRA_RESTAPI_ENV=os.environ["DIOPTRA_RESTAPI_ENV"],
                effective_mode=settings.CONFIG_NAME,
            )

    from .bootstrap import bind_dependencies, register_providers
    from .errors import register_error_handlers
    from .routes import register_routes
    from .v1.users.service import load_user as v1_load_user

    monkey_patch_flask_restx()

    app: Flask = Flask(__name__)
    app.config.from_object(settings)
    app.extensions["dioptra_settings"] = settings

    api: Api = Api(
        app,
        title="Dioptra REST API",
        version=DIOPTRA_VERSION,
        doc=app.config["DIOPTRA_SWAGGER_PATH"],
        url_scheme=app.config["DIOPTRA_BASE_URL"],
    )

    register_routes(api)
    register_error_handlers(api)

    login_manager.user_loader(v1_load_user)

    db.init_app(app)
    login_manager.init_app(app)

    if settings.CONFIG_NAME == "dev":
        cors.init_app(
            app, resources={r"/api/*": {"origins": app.config["DIOPTRA_CORS_ORIGIN"]}}
        )

    with app.app_context():
        migrate.init_app(app, db, render_as_batch=True)

    @app.route("/health")
    def health():
        """An endpoint for monitoring if the REST API is responding to requests."""
        log = LOGGER.new(request_id=str(uuid.uuid4()))  # noqa: F841
        return jsonify({"status": "healthy", "version": DIOPTRA_VERSION})

    if injector is None:

        def configure(binder: Binder) -> None:
            bind_dependencies(binder, settings)

        modules: List[Callable[..., Any]] = [configure]
        register_providers(modules)
        injector = Injector(modules)

    setup_injection(api, injector)

    return app
