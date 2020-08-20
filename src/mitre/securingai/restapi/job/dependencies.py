import os
from dataclasses import dataclass
from typing import Any, Callable, List

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


def bind_dependencies(binder: Binder) -> None:
    redis_conn: Redis = Redis.from_url(os.getenv("RQ_REDIS_URI", "redis://"))
    run_mlflow: str = "mitre.securingai.restapi.shared.task.run_mlflow_task"

    configuration: RQServiceConfiguration = RQServiceConfiguration(
        redis=redis_conn,
        run_mlflow=run_mlflow,
    )

    binder.bind(RQServiceConfiguration, to=configuration, scope=singleton)


def register_providers(modules: List[Callable[..., Any]]) -> None:
    modules.append(RQServiceModule)
