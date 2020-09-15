import uuid
from typing import Any, Callable, List, Optional

import structlog
from flask import Flask, jsonify
from flask_injector import FlaskInjector
from flask_migrate import Migrate
from flask_restx import Api
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect


LOGGER = structlog.get_logger()

csrf = CSRFProtect()
db = SQLAlchemy()
migrate = Migrate()


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
        app, title="Securing AI Machine Learning Model Endpoint", version="0.0.0",
    )
    modules: List[Callable[..., Any]] = [bind_dependencies]

    register_routes(api, app)
    register_error_handlers(api)
    register_providers(modules)
    csrf.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    @app.route("/health")
    def health():
        log = LOGGER.new(request_id=str(uuid.uuid4()))  # noqa: F841
        return jsonify("healthy")

    if not inject_dependencies:
        return app

    FlaskInjector(app=app, modules=modules)

    return app
