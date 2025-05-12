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
from collections.abc import Sequence
from typing import Any, Protocol


class EntryPointParameterProtocol(Protocol):
    parameter_type: str
    name: str
    default_value: str | None


class EntryPointProtocol(Protocol):
    @property
    def task_graph(self) -> str: ...  # noqa: E704

    @property
    def parameters(self) -> Sequence[EntryPointParameterProtocol]: ...  # noqa: E704


class PluginTaskParameterTypeProtocol(Protocol):
    @property
    def name(self) -> str: ...  # noqa: E704

    @property
    def structure(self) -> dict[str, Any] | None: ...  # noqa: E704


class PluginTaskInputParameterProtocol(Protocol):
    parameter_number: int
    name: str
    required: bool

    @property
    def parameter_type(self) -> PluginTaskParameterTypeProtocol: ...  # noqa: E704


class PluginTaskOutputParameterProtocol(Protocol):
    parameter_number: int
    name: str

    @property
    def parameter_type(self) -> PluginTaskParameterTypeProtocol: ...  # noqa: E704


class PluginTaskProtocol(Protocol):
    plugin_task_name: str

    @property
    def input_parameters(  # noqa: E704
        self,
    ) -> Sequence[PluginTaskInputParameterProtocol]: ...

    @property
    def output_parameters(  # noqa: E704
        self,
    ) -> Sequence[PluginTaskOutputParameterProtocol]: ...


class PluginFileProtocol(Protocol):
    filename: str

    @property
    def tasks(self) -> Sequence[PluginTaskProtocol]: ...  # noqa: E704


class PluginProtocol(Protocol):
    name: str


class PluginPluginFileProtocol(Protocol):
    @property
    def plugin(self) -> PluginProtocol: ...  # noqa: E704

    @property
    def plugin_file(self) -> PluginFileProtocol: ...  # noqa: E704
