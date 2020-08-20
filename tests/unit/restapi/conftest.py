from typing import Any, List

import pytest
from flask import Flask
from flask_injector import FlaskInjector, request
from flask_sqlalchemy import SQLAlchemy
from injector import Binder, Injector
from redis import Redis


@pytest.fixture
def dependency_modules() -> List[Any]:
    from mitre.securingai.restapi.job.dependencies import (
        RQServiceConfiguration,
        RQServiceModule,
    )

    def configure(binder: Binder) -> None:
        binder.bind(
            interface=RQServiceConfiguration,
            to=RQServiceConfiguration(
                redis=Redis.from_url("redis://"),
                run_mlflow="mitre.securingai.restapi.shared.task.service.run_mlflow_task",
            ),
            scope=request,
        )

    return [configure, RQServiceModule()]


@pytest.fixture
def dependency_injector(dependency_modules: List[Any]) -> Injector:
    return Injector(dependency_modules)


@pytest.fixture
def app(dependency_modules: List[Any]) -> Flask:
    from mitre.securingai.restapi import create_app

    app: Flask = create_app(env="test", inject_dependencies=False)
    FlaskInjector(app=app, modules=dependency_modules)

    return app


@pytest.fixture
def db(app: Flask) -> SQLAlchemy:
    from mitre.securingai.restapi.app import db

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield db
        db.drop_all()
        db.session.commit()
