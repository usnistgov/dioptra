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
from typing import Any, BinaryIO, List

import pytest
from _pytest.monkeypatch import MonkeyPatch
from boto3.session import Session
from botocore.client import BaseClient
from flask import Flask
from flask_injector import FlaskInjector, request
from flask_restx import Api
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
    from dioptra.restapi.experiment.dependencies import (
        ExperimentRegistrationFormSchemaModule,
    )
    from dioptra.restapi.job.dependencies import (
        JobFormSchemaModule,
        RQServiceConfiguration,
        RQServiceModule,
    )
    from dioptra.restapi.queue.dependencies import QueueRegistrationFormSchemaModule
    from dioptra.restapi.task_plugin.dependencies import (
        TaskPluginUploadFormSchemaModule,
    )
    from dioptra.restapi.user.dependencies import (
        PasswordServiceModule,
        UserRegistrationFormSchemaModule,
        _bind_password_service_configuration,
    )

    def _bind_rq_service_configuration(binder: Binder) -> None:
        configuration: RQServiceConfiguration = RQServiceConfiguration(
            redis=Redis.from_url("redis://"),
            run_mlflow="dioptra.rq.tasks.run_mlflow_task",
            run_task_engine="dioptra.rq.tasks.run_task_engine",
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
        ExperimentRegistrationFormSchemaModule(),
        JobFormSchemaModule(),
        PasswordServiceModule(),
        QueueRegistrationFormSchemaModule(),
        RQServiceModule(),
        TaskPluginUploadFormSchemaModule(),
        UserRegistrationFormSchemaModule(),
    ]


@pytest.fixture
def dependency_injector(dependency_modules: List[Any]) -> Injector:
    return Injector(dependency_modules)


@pytest.fixture
def app(dependency_modules: List[Any], monkeypatch: MonkeyPatch) -> Flask:
    import dioptra.restapi.routes
    from dioptra.restapi import create_app

    # Override register_routes in dioptra.restapi.routes to enable testing of endpoints
    # that are under development.
    def register_test_routes(api: Api, app: Flask) -> None:
        from dioptra.restapi.experiment import register_routes as attach_experiment
        from dioptra.restapi.job import register_routes as attach_job
        from dioptra.restapi.queue import register_routes as attach_job_queue
        from dioptra.restapi.task_plugin import register_routes as attach_task_plugin
        from dioptra.restapi.user import register_routes as attach_user

        # Add routes
        attach_experiment(api, app)
        attach_job(api, app)
        attach_job_queue(api, app)
        attach_task_plugin(api, app)
        attach_user(api, app)

    monkeypatch.setattr(dioptra.restapi.routes, "register_routes", register_test_routes)

    app: Flask = create_app(env="test", inject_dependencies=False)
    FlaskInjector(app=app, modules=dependency_modules)

    return app


@pytest.fixture
def db(app: Flask) -> SQLAlchemy:
    from dioptra.restapi.app import db

    with app.app_context():
        db.drop_all()
        db.create_all()
        yield db
        db.drop_all()
        db.session.commit()


@pytest.fixture(autouse=True)
def seed_database(db):
    from dioptra.restapi.job.model import job_statuses

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
