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

from dataclasses import dataclass
from typing import Any, Callable

from injector import Binder, Module, provider
from passlib.context import CryptContext

from dioptra.restapi.shared.password.service import PasswordService


@dataclass
class PasswordServiceConfiguration(object):
    crypt_context: CryptContext


class PasswordServiceModule(Module):
    @provider
    def provide_password_service_module(
        self, configuration: PasswordServiceConfiguration
    ) -> PasswordService:
        return PasswordService(crypt_context=configuration.crypt_context)


def _bind_password_service_configuration(binder: Binder):
    configuration: PasswordServiceConfiguration = PasswordServiceConfiguration(
        crypt_context=CryptContext(
            schemes=["pbkdf2_sha256"],
            pbkdf2_sha256__default_rounds=30000,
        ),
    )

    binder.bind(PasswordServiceConfiguration, to=configuration)


def bind_dependencies(binder: Binder) -> None:
    """Binds interfaces to implementations within the main application.

    Args:
        binder: A :py:class:`~injector.Binder` object.
    """
    _bind_password_service_configuration(binder)


def register_providers(modules: list[Callable[..., Any]]) -> None:
    """Registers type providers within the main application.

    Args:
        modules: A list of callables used for configuring the dependency injection
            environment.
    """
    modules.append(PasswordServiceModule)
