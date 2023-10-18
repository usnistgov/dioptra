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
"""Binding configurations to shared services using dependency injection."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Callable, List, Optional

from boto3.session import Session
from botocore.client import BaseClient
from flask_injector import request
from injector import Binder, Module, provider
from redis import Redis

from dioptra.restapi.shared.rq.service import RQService

from .schema import JobFormSchema


class JobFormSchemaModule(Module):
    @provider
    def provide_job_form_schema_module(self) -> JobFormSchema:
        return JobFormSchema()


@dataclass
class RQServiceConfiguration(object):
    redis: Redis
    run_mlflow: str
    run_task_engine: str


class RQServiceModule(Module):
    @request
    @provider
    def provide_rq_service_module(
        self, configuration: RQServiceConfiguration
    ) -> RQService:
        return RQService(
            redis=configuration.redis,
            run_mlflow=configuration.run_mlflow,
            run_task_engine=configuration.run_task_engine,
        )


def _bind_rq_service_configuration(binder: Binder):
    redis_conn: Redis = Redis.from_url(os.getenv("RQ_REDIS_URI", "redis://"))
    run_mlflow: str = "dioptra.rq.tasks.run_mlflow_task"
    run_task_engine: str = "dioptra.rq.tasks.run_task_engine_task"

    configuration: RQServiceConfiguration = RQServiceConfiguration(
        redis=redis_conn, run_mlflow=run_mlflow, run_task_engine=run_task_engine
    )

    binder.bind(RQServiceConfiguration, to=configuration, scope=request)


def _bind_s3_service_configuration(binder: Binder) -> None:
    s3_endpoint_url: Optional[str] = os.getenv("MLFLOW_S3_ENDPOINT_URL")

    s3_session: Session = Session()
    s3_client: BaseClient = s3_session.client("s3", endpoint_url=s3_endpoint_url)

    binder.bind(Session, to=s3_session, scope=request)
    binder.bind(BaseClient, to=s3_client, scope=request)


def bind_dependencies(binder: Binder) -> None:
    """Binds interfaces to implementations within the main application.

    Args:
        binder: A :py:class:`~injector.Binder` object.
    """
    _bind_rq_service_configuration(binder)
    _bind_s3_service_configuration(binder)


def register_providers(modules: List[Callable[..., Any]]) -> None:
    """Registers type providers within the main application.

    Args:
        modules: A list of callables used for configuring the dependency injection
            environment.
    """
    modules.append(JobFormSchemaModule)
    modules.append(RQServiceModule)
