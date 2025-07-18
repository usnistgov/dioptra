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
from typing import Any, BinaryIO, List

import pytest
import sqlalchemy
from boto3.session import Session
from botocore.client import BaseClient
from faker import Faker
from flask import Flask
from flask.testing import FlaskClient
from injector import Binder, Injector
from mlflow.tracking import set_tracking_uri
from redis import Redis
from requests import ConnectionError
from requests import Session as RequestsSession
from sqlalchemy.orm import Session as DBSession

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.client import DioptraClient
from dioptra.restapi.db import db as restapi_db
from dioptra.restapi.db.repository.drafts import DraftsRepository
from dioptra.restapi.db.repository.experiments import ExperimentRepository
from dioptra.restapi.db.repository.groups import GroupRepository
from dioptra.restapi.db.repository.queues import QueueRepository
from dioptra.restapi.db.repository.types import TypeRepository
from dioptra.restapi.db.repository.users import UserRepository
from dioptra.restapi.db.repository.utils import DeletionPolicy, ExistenceResult
from dioptra.restapi.db.unit_of_work import UnitOfWork
from dioptra.restapi.request_scope import request

from .lib import db as libdb
from .lib.client import DioptraFlaskClientSession


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


@pytest.fixture(scope="session")
def dependency_modules() -> List[Any]:
    from mlflow import MlflowClient

    from dioptra.restapi.bootstrap import (
        JobRunStoreModule,
        PasswordServiceModule,
        RQServiceConfiguration,
        RQServiceV1Module,
        _bind_password_service_configuration,
    )

    from .lib.mock_mlflow import MockMlflowClient

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

    def _bind_job_run_store_configuration(binder: Binder):
        binder.bind(interface=MlflowClient, to=MockMlflowClient(), scope=request)

    def configure(binder: Binder) -> None:
        _bind_password_service_configuration(binder)
        _bind_rq_service_configuration(binder)
        _bind_s3_service_configuration(binder)
        _bind_job_run_store_configuration(binder)

    return [configure, PasswordServiceModule, RQServiceV1Module, JobRunStoreModule]


@pytest.fixture(scope="session")
def dependency_injector(dependency_modules: List[Any]) -> Injector:
    return Injector(dependency_modules)


@pytest.fixture(scope="function")
def db_session(flask_app: Flask) -> DBSession:
    with flask_app.app_context():
        # following the recipe as described here:
        # https://docs.sqlalchemy.org/en/20/orm/session_transaction.html
        # append the reference below to get to the exact location
        #  #joining-a-session-into-an-external-transaction-such-as-for-test-suites
        """Creates a new database session for each test function."""
        connection = restapi_db.engine.connect()
        transaction = connection.begin()

        DBSession = sqlalchemy.orm.sessionmaker(
            connection, join_transaction_mode="create_savepoint"
        )

        with DBSession() as session:
            old = restapi_db.session
            restapi_db.session = session
            yield session
            restapi_db.session = old

        transaction.rollback()
        connection.close()


@pytest.fixture(scope="session")
def flask_app(dependency_modules: List[Any]) -> Flask:
    from dioptra.restapi import create_app

    injector = Injector(dependency_modules)
    app = create_app(env="test_no_login", injector=injector)

    with app.app_context():
        # sqlite specific fix, see:
        # https://docs.sqlalchemy.org/en/20/dialects/sqlite.html
        @sqlalchemy.event.listens_for(restapi_db.engine, "connect")
        def do_connect(dbapi_connection, connection_record):
            # disable sqlite3's emitting of the BEGIN statement entirely.
            dbapi_connection.isolation_level = None

        @sqlalchemy.event.listens_for(restapi_db.engine, "begin")
        def do_begin(conn):
            # emit our own BEGIN.   sqlite3 still emits COMMIT/ROLLBACK correctly
            conn.exec_driver_sql("BEGIN")

        restapi_db.drop_all()
        restapi_db.create_all()
        libdb.setup_ontology(restapi_db.session)

    yield app

    with app.app_context():
        restapi_db.drop_all()
        restapi_db.session.commit()


@pytest.fixture(scope="function")
def client(flask_app: Flask, db_session: DBSession) -> FlaskClient:
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def dioptra_client(client: FlaskClient) -> DioptraClient[DioptraResponseProtocol]:
    return DioptraClient[DioptraResponseProtocol](DioptraFlaskClientSession(client))


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


@pytest.fixture
def fake_data(faker: Faker) -> libdb.FakeData:
    return libdb.FakeData(faker)


@pytest.fixture
def account(db_session: DBSession, fake_data: libdb.FakeData) -> libdb.FakeAccount:
    new_account = fake_data.account()
    db_session.add(new_account.user)
    db_session.add(new_account.group)
    db_session.commit()
    return new_account


@pytest.fixture(
    params=list(DeletionPolicy),
    ids=[dp.name.lower() for dp in DeletionPolicy],
)
def deletion_policy(request):
    """
    A simple parameterized fixture that makes it easy to combine all deletion
    policy values with other things in a parameterized unit test.  This just
    produces the DeletionPolicy enum values.
    """
    return request.param


@pytest.fixture(
    params=list(ExistenceResult), ids=[e.name.lower() for e in ExistenceResult]
)
def existence_status(request):
    """
    A simple parameterized fixture that makes it easy to combine all status
    values (ExistenceResult's) with other things in a parameterized unit test.
    This just produces the ExistenceResult enum values.
    """
    return request.param


@pytest.fixture
def group_repo(db_session: DBSession) -> GroupRepository:
    repo = GroupRepository(db_session)

    return repo


@pytest.fixture
def user_repo(db_session: DBSession) -> UserRepository:
    repo = UserRepository(db_session)

    return repo


@pytest.fixture
def queue_repo(db_session: DBSession) -> QueueRepository:
    repo = QueueRepository(db_session)

    return repo


@pytest.fixture
def drafts_repo(db_session: DBSession) -> DraftsRepository:
    repo = DraftsRepository(db_session)

    return repo


@pytest.fixture
def experiment_repo(db_session: DBSession) -> ExperimentRepository:
    repo = ExperimentRepository(db_session)

    return repo


@pytest.fixture
def type_repo(db_session: DBSession) -> TypeRepository:
    repo = TypeRepository(db_session)

    return repo


@pytest.fixture
def uow(db_session: DBSession) -> UnitOfWork:
    return UnitOfWork()
