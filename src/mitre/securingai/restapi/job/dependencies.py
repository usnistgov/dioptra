import os
from dataclasses import dataclass
from typing import Any, Callable, List

from boto3.session import Session
from botocore.client import BaseClient
from flask_injector import request
from injector import Binder, Module, provider, singleton
from redis import Redis

from .service import RQService


@dataclass
class RQServiceConfiguration(object):
    redis: Redis
    run_mlflow: str


class RQServiceModule(Module):
    @singleton
    @provider
    def provide_rq_service_module(
        self, configuration: RQServiceConfiguration
    ) -> RQService:
        return RQService(redis=configuration.redis, run_mlflow=configuration.run_mlflow)


def _bind_rq_service_configuration(binder: Binder):
    redis_conn: Redis = Redis.from_url(os.getenv("RQ_REDIS_URI", "redis://"))
    run_mlflow: str = "mitre.securingai.restapi.shared.task.run_mlflow_task"

    configuration: RQServiceConfiguration = RQServiceConfiguration(
        redis=redis_conn,
        run_mlflow=run_mlflow,
    )

    binder.bind(RQServiceConfiguration, to=configuration, scope=singleton)


def _bind_s3_service_configuration(binder: Binder) -> None:
    s3_endpoint_url: str = os.getenv("MLFLOW_S3_ENDPOINT_URL")

    s3_session: Session = Session()
    s3_client: BaseClient = s3_session.client("s3", endpoint_url=s3_endpoint_url)

    binder.bind(Session, to=s3_session, scope=request)
    binder.bind(BaseClient, to=s3_client, scope=request)


def bind_dependencies(binder: Binder) -> None:
    _bind_rq_service_configuration(binder)
    _bind_s3_service_configuration(binder)


def register_providers(modules: List[Callable[..., Any]]) -> None:
    modules.append(RQServiceModule)
