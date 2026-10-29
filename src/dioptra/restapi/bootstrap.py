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
"""A module for binding configurations to shared services using dependency injection."""

from dataclasses import dataclass
from typing import Any, Callable, List

from injector import Binder, Module, provider
from mlflow import MlflowClient
from passlib.context import CryptContext
from redis import Redis

from dioptra.restapi.config import BaseConfig
from dioptra.restapi.db.unit_of_work import UnitOfWork
from dioptra.restapi.request_scope import request
from dioptra.restapi.service_context import ServiceContext
from dioptra.restapi.v1.shared.job_queue import JobQueueProtocol
from dioptra.restapi.v1.shared.job_run_store import (
    JobRunStoreProtocol,
    MlFlowJobRunStore,
)
from dioptra.restapi.v1.shared.password_service import PasswordService
from dioptra.restapi.v1.shared.rq_service import RQServiceV1


class JobRunStoreModule(Module):
    """Provide the MLflow-backed job run store in request scope."""

    @request
    @provider
    def provide_job_run_store_module(
        self,
        client: MlflowClient,
    ) -> JobRunStoreProtocol:
        """Wrap the injected MLflow client in a job run store.

        Args:
            client: MLflow client used for run storage.

        Returns:
            The request-scoped MLflow-backed job run store.
        """
        return MlFlowJobRunStore(client)


@dataclass
class RQServiceConfiguration(object):
    """Hold the Redis connection supplied to request-scoped RQ services.

    Args:
        redis: Connection used by the RQ service provider.
    """

    redis: Redis


class RQServiceV1Module(Module):
    """Provide RQ services using the configured Redis connection."""

    @request
    @provider
    def provide_rq_service_module(
        self, configuration: RQServiceConfiguration
    ) -> JobQueueProtocol:
        """Create an RQ service from the injected Redis configuration.

        Args:
            configuration: Redis connection configuration.

        Returns:
            A request-scoped RQ service using that connection.
        """
        return RQServiceV1(redis=configuration.redis)


class ServiceContextModule(Module):
    @request
    @provider
    def provide_service_context_module(
        self,
        uow: UnitOfWork,
        job_queue: JobQueueProtocol,
        job_run_store: JobRunStoreProtocol,
    ) -> ServiceContext:
        return ServiceContext(
            uow=uow,
            job_queue=job_queue,
            job_run_store=job_run_store,
        )


@dataclass
class PasswordServiceConfiguration(object):
    """Hold the cryptographic context used by password services.

    Args:
        crypt_context: Context used to hash and verify passwords.
    """

    crypt_context: CryptContext


class PasswordServiceModule(Module):
    """Provide password services using the configured cryptographic context."""

    @provider
    def provide_password_service_module(
        self, configuration: PasswordServiceConfiguration
    ) -> PasswordService:
        """Create a password service from the injected cryptographic context.

        Args:
            configuration: Password hashing configuration.

        Returns:
            A password service using that context.
        """
        return PasswordService(crypt_context=configuration.crypt_context)


def _bind_rq_service_configuration(binder: Binder, settings: BaseConfig):
    """Bind a Redis connection constructed from the resolved API URI."""
    redis_conn: Redis = Redis.from_url(settings.RQ_REDIS_URI)
    configuration: RQServiceConfiguration = RQServiceConfiguration(redis=redis_conn)
    binder.bind(RQServiceConfiguration, to=configuration, scope=request)


def _bind_job_run_store_configuration(binder: Binder, settings: BaseConfig):
    """Bind an MLflow client using the resolved tracking URI."""
    tracking_uri = settings.MLFLOW_TRACKING_URI
    binder.bind(MlflowClient, to=MlflowClient(tracking_uri=tracking_uri), scope=request)


def _bind_password_service_configuration(binder: Binder):
    """Bind the password hashing configuration used by the provider."""
    configuration: PasswordServiceConfiguration = PasswordServiceConfiguration(
        crypt_context=CryptContext(
            schemes=["pbkdf2_sha256"],
            pbkdf2_sha256__default_rounds=30000,
        ),
    )

    binder.bind(PasswordServiceConfiguration, to=configuration)


def bind_dependencies(binder: Binder, settings: BaseConfig) -> None:
    """Binds interfaces to implementations within the main application.

    Args:
        binder: A :py:class:`~injector.Binder` object.
        settings: The application's validated, resolved configuration.
    """

    _bind_rq_service_configuration(binder, settings)
    _bind_password_service_configuration(binder)
    _bind_job_run_store_configuration(binder, settings)


def register_providers(modules: List[Callable[..., Any]]) -> None:
    """Register the application service providers in an injector module list.

    Args:
        modules: List to which the provider module classes are appended. The list
            is modified in place.
    """

    modules.append(JobRunStoreModule)
    modules.append(RQServiceV1Module)
    modules.append(ServiceContextModule)
    modules.append(PasswordServiceModule)
