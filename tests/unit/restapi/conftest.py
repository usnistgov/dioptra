import io
import tarfile
from typing import Any, BinaryIO, List

import pytest
from boto3.session import Session
from botocore.client import BaseClient
from flask import Flask
from flask_injector import FlaskInjector, request
from flask_sqlalchemy import SQLAlchemy
from injector import Binder, Injector
from redis import Redis


@pytest.fixture(scope="session")
def task_plugins_dir(tmp_path_factory):
    base_dir = tmp_path_factory.getbasetemp()
    artifacts_dir = tmp_path_factory.mktemp("artifacts", numbered=False)
    models_dir = tmp_path_factory.mktemp("models", numbered=False)

    for fn in ["__init__.py", "mlflow.py"]:
        (artifacts_dir / fn).touch()

    for fn in ["__init__.py", "keras.py", "data.json"]:
        (models_dir / fn).touch()

    return base_dir


@pytest.fixture
def workflow_tar_gz():
    workflow_tar_gz_fileobj: BinaryIO = io.BytesIO()

    with tarfile.open(fileobj=workflow_tar_gz_fileobj, mode="w:gz") as f, io.BytesIO(
        initial_bytes=b"data"
    ) as data:
        tarinfo = tarfile.TarInfo(name="MLproject")
        tarinfo.size = len(data.getbuffer())
        f.addfile(tarinfo=tarinfo, fileobj=data)

    workflow_tar_gz_fileobj.seek(0)
    yield workflow_tar_gz_fileobj
    workflow_tar_gz_fileobj.close()


@pytest.fixture
def task_plugin_archive():
    archive_fileobj: BinaryIO = io.BytesIO()

    with tarfile.open(fileobj=archive_fileobj, mode="w:gz") as f, io.BytesIO(
        initial_bytes=b"# init file"
    ) as f_init, io.BytesIO(initial_bytes=b"# plugin module") as f_plugin_module:
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
    from mitre.securingai.restapi.job.dependencies import (
        RQServiceConfiguration,
        RQServiceModule,
    )

    def _bind_s3_service_configuration(binder: Binder) -> None:
        s3_session: Session = Session()
        s3_client: BaseClient = s3_session.client("s3")

        binder.bind(Session, to=s3_session, scope=request)
        binder.bind(BaseClient, to=s3_client, scope=request)

    def configure(binder: Binder) -> None:
        binder.bind(
            interface=RQServiceConfiguration,
            to=RQServiceConfiguration(
                redis=Redis.from_url("redis://"),
                run_mlflow="mitre.securingai.rq.tasks.run_mlflow_task",
            ),
            scope=request,
        )
        _bind_s3_service_configuration(binder)

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


@pytest.fixture(autouse=True)
def seed_database(db):
    from mitre.securingai.restapi.job.model import job_statuses

    db.session.execute(
        job_statuses.insert(),
        [
            {"status": "queued"},
            {"status": "started"},
            {"status": "deferred"},
            {"status": "finished"},
            {"status": "failed"},
        ],
    )
    db.session.commit()
