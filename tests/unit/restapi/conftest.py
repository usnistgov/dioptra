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
from __future__ import annotations

import io
import tarfile
import time
from pathlib import Path
from typing import Any, BinaryIO, Iterable, List

import pytest
import requests
from boto3.session import Session
from botocore.client import BaseClient
from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from injector import Binder, Injector
from mlflow.tracking import set_tracking_uri
from redis import Redis
from requests import ConnectionError
from requests import Session as RequestsSession

from dioptra.restapi.db import db as restapi_db
from dioptra.restapi.v1.shared.request_scope import request

from .lib import db as libdb
from .lib.server import FlaskTestServer


@pytest.fixture
def task_plugin_archive():
    archive_fileobj: BinaryIO = io.BytesIO()

    with (
        tarfile.open(fileobj=archive_fileobj, mode="w:gz") as f,
        io.BytesIO(initial_bytes=b"# init file") as f_init,
        io.BytesIO(initial_bytes=b"# plugin module") as f_plugin_module,
    ):
        tarinfo_init = tarfile.TarInfo(name="new_plugin_module/__init__.py")
        tarinfo_init.size = len(f_init.getbuffer())
        f.addfile(tarinfo=tarinfo_init, fileobj=f_init)

        tarinfo_plugin_module = tarfile.TarInfo(
            name="new_plugin_module/plugin_module.py"
        )
        tarinfo_plugin_module.size = len(f_plugin_module.getbuffer())
        f.addfile(tarinfo=tarinfo_plugin_module, fileobj=f_plugin_module)

    archive_fileobj.seek(0)
    yield archive_fileobj
    archive_fileobj.close()


@pytest.fixture
def dependency_modules() -> List[Any]:
    from dioptra.restapi.bootstrap import (
        PasswordServiceModule,
        RQServiceConfiguration,
        RQServiceV1Module,
        _bind_password_service_configuration,
    )

    def _bind_rq_service_configuration(binder: Binder) -> None:
        configuration: RQServiceConfiguration = RQServiceConfiguration(
            redis=Redis.from_url("redis://"),
        )

        binder.bind(
            interface=RQServiceConfiguration,
            to=configuration,
            scope=request,
        )

    def _bind_s3_service_configuration(binder: Binder) -> None:
        s3_session: Session = Session()
        s3_client: BaseClient = s3_session.client("s3")

        binder.bind(Session, to=s3_session, scope=request)
        binder.bind(BaseClient, to=s3_client, scope=request)

    def configure(binder: Binder) -> None:
        _bind_password_service_configuration(binder)
        _bind_rq_service_configuration(binder)
        _bind_s3_service_configuration(binder)

    return [
        configure,
        PasswordServiceModule,
        RQServiceV1Module,
    ]


@pytest.fixture
def dependency_injector(dependency_modules: List[Any]) -> Injector:
    return Injector(dependency_modules)


@pytest.fixture
def app(dependency_modules: List[Any]) -> Flask:
    from dioptra.restapi import create_app

    injector = Injector(dependency_modules)
    app = create_app(env="test_no_login", injector=injector)

    yield app


@pytest.fixture
def db(app: Flask) -> SQLAlchemy:
    with app.app_context():
        restapi_db.drop_all()
        restapi_db.create_all()
        yield restapi_db
        restapi_db.drop_all()
        restapi_db.session.commit()


@pytest.fixture(autouse=True)
def seed_database(db: SQLAlchemy):
    libdb.setup_ontology(db.session)


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture
def flask_test_server(tmp_path: Path, http_client: RequestsSession):
    """Start a Flask test server.

    Args:
        tmp_path: The path to the temporary directory.
        http_client: A Requests session client.
    """
    sqlite_path = tmp_path / "dioptra-test.db"
    server = FlaskTestServer(sqlite_path=sqlite_path)
    server.upgrade_db()
    with server:
        wait_for_healthcheck_success(http_client)
        yield


@pytest.fixture
def http_client() -> Iterable[RequestsSession]:
    """A Requests session for accessing the API.

    Yields:
        A Requests session.
    """
    with requests.Session() as s:
        yield s


@pytest.fixture(autouse=True)
def create_mlruns(tmp_path):
    path = Path(tmp_path / "mlruns")
    path.mkdir()
    set_tracking_uri(path)


def wait_for_healthcheck_success(client: RequestsSession, timeout: int = 10) -> None:
    """Wait for the healthcheck endpoint to return a successful response.

    Args:
        client: A Requests session client.
        timeout: The maximum number of seconds to wait for the healthcheck endpoint to
            return a successful response.

    Raises:
        TimeoutError: If the healthcheck endpoint does not return a successful response
            within the specified timeout.
    """

    class StubResponse(object):
        """Stubbed response to use when the client experiences a connection error."""

        def json(self) -> str:
            """Return an empty string."""
            return ""

    healthcheck_url = "http://localhost:5000/health"
    time_elapsed = 0

    try:
        healthcheck = client.get(healthcheck_url)

    except ConnectionError:
        healthcheck = StubResponse()

    time_start = time.time()

    while healthcheck.json() != "healthy":
        if time_elapsed > timeout:
            raise TimeoutError("Healthcheck failed to return healthy status")

        time.sleep(0.1)

        try:
            healthcheck = client.get(healthcheck_url)

        except ConnectionError:
            healthcheck = StubResponse()

        time_elapsed = time.time() - time_start
