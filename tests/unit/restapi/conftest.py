from typing import Any, List

import pytest
from flask import Flask
from flask_injector import FlaskInjector
from injector import Injector


@pytest.fixture
def dependency_modules() -> List[Any]:
    return []


@pytest.fixture
def dependency_injector(dependency_modules: List[Any]) -> Injector:
    return Injector(dependency_modules)


@pytest.fixture
def app(dependency_modules: List[Any]) -> Flask:
    from mitre.securingai.restapi import create_app

    app: Flask = create_app(env="test", inject_dependencies=False)
    FlaskInjector(app=app, modules=dependency_modules)

    return app
