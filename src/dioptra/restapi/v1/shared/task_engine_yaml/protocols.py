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
from typing import Any, Protocol


class EntryPointParameterProtocol(Protocol):
    parameter_type: str
    name: str
    default_value: str | None


class EntryPointProtocol(Protocol):
    task_graph: str
    parameters: list[EntryPointParameterProtocol]


class PluginTaskParameterTypeProtocol(Protocol):
    name: str
    structure: dict[str, Any] | None


class PluginTaskInputParameterProtocol(Protocol):
    parameter_number: int
    name: str
    required: bool
    parameter_type: PluginTaskParameterTypeProtocol


class PluginTaskOutputParameterProtocol(Protocol):
    parameter_number: int
    name: str
    parameter_type: PluginTaskParameterTypeProtocol


class PluginTaskProtocol(Protocol):
    plugin_task_name: str
    input_parameters: list[PluginTaskInputParameterProtocol]
    output_parameters: list[PluginTaskOutputParameterProtocol]


class PluginFileProtocol(Protocol):
    filename: str
    tasks: list[PluginTaskProtocol]


class PluginProtocol(Protocol):
    name: str


class PluginPluginFileProtocol(Protocol):
    plugin: PluginProtocol
    plugin_file: PluginFileProtocol
