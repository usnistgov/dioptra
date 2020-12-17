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

from .__version__ import __version__ as API_VERSION

LOGGER = structlog.get_logger()

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
        title="Securing AI Machine Learning Model Endpoint",
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
        log = LOGGER.new(request_id=str(uuid.uuid4()))  # noqa: F841
        return jsonify("healthy")

    if not inject_dependencies:
        return app

    FlaskInjector(app=app, modules=modules)

    return app
