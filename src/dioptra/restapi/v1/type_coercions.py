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
import json
from collections.abc import Sequence
from typing import Any, Final, cast

from dioptra.restapi.db.models.entry_points import (
    EntryPointArtifactOutputParameter,
    EntryPointParameterValue,
)
from dioptra.restapi.db.models.plugins import PluginTaskOutputParameter
from dioptra.restapi.errors import (
    ArtifactParameterTypeMismatchError,
    EntrypointParameterTypeMismatchError,
)

JsonType = dict[str, Any] | list[Any]
GlobalParameterType = str | float | int | bool | dict[str, Any] | list[Any] | None


BOOLEAN_PARAM_TYPE: Final[str] = "boolean"
FLOAT_PARAM_TYPE: Final[str] = "float"
INTEGER_PARAM_TYPE: Final[str] = "integer"
LIST_PARAM_TYPE: Final[str] = "list"
MAPPING_PARAM_TYPE: Final[str] = "mapping"
STRING_PARAM_TYPE: Final[str] = "string"


def coerce_to_type(x: str | None, type_name: str) -> GlobalParameterType:
    coerce_fn_registry = {
        BOOLEAN_PARAM_TYPE: to_boolean_type,
        FLOAT_PARAM_TYPE: to_float_type,
        INTEGER_PARAM_TYPE: to_integer_type,
        LIST_PARAM_TYPE: to_list_type,
        MAPPING_PARAM_TYPE: to_mapping_type,
        STRING_PARAM_TYPE: to_string_type,
    }

    if type_name not in coerce_fn_registry:
        raise ValueError(f"Invalid parameter type: {type_name}.")

    if x is None:
        return None

    coerce_fn = coerce_fn_registry[type_name]
    return cast(GlobalParameterType, coerce_fn(x))


def to_string_type(x: str) -> str:
    return x


def to_boolean_type(x: str) -> bool:
    if x.lower() not in {"true", "false"}:
        raise ValueError(f"Not a boolean: {x}")

    return x.lower() == "true"


def to_float_type(x: str) -> float:
    # TODO: Handle coercion failures
    return float(x)


def to_integer_type(x: str) -> int:
    # TODO: Handle coercion failures
    return int(x)


def to_list_type(x: str) -> list[Any]:
    # TODO: Handle coercion failures
    x_coerced = cast(JsonType, json.loads(x))

    if not isinstance(x_coerced, list):
        raise ValueError(f"Not a list: {x}")

    return x_coerced


def to_mapping_type(x: str) -> dict[str, Any]:
    # TODO: Handle coercion failures
    x_coerced = cast(JsonType, json.loads(x))

    if not isinstance(x_coerced, dict):
        raise ValueError(f"Not a mapping: {x}")

    return x_coerced


def coerce_entrypoint_param_types(
    parameters: Sequence[EntryPointParameterValue],
) -> dict[str, Any]:
    """Coerce job-provided entrypoint parameter values to declared types."""
    param_values = []
    param_names = []
    correct_types = []
    coerced_params = {}

    for param in parameters:
        passed_value = param.value

        try:
            coerced = coerce_to_type(
                x=passed_value,
                type_name=param.parameter.parameter_type,
            )
            coerced_params[param.parameter.name] = coerced
        except ValueError:
            param_values.append(passed_value)
            param_names.append(param.parameter.name)
            correct_types.append(param.parameter.parameter_type)

    if param_names:
        raise EntrypointParameterTypeMismatchError(
            values=param_values,
            parameter_names=param_names,
            correct_types=correct_types,
        )

    return coerced_params


def check_artifact_param_type_mismatch(
    expected_parameters: list[EntryPointArtifactOutputParameter],
    given_parameters: list[PluginTaskOutputParameter],
) -> None:
    """Raise when artifact output parameter types differ from expected types."""
    parameter_names = []
    given_types = []
    expected_types = []

    for expected, given in zip(
        sorted(expected_parameters, key=lambda x: x.parameter_number),
        sorted(given_parameters, key=lambda x: x.parameter_number),
    ):
        if expected.parameter_type.resource_id != given.parameter_type.resource_id:
            parameter_names.append(expected.name)
            given_types.append(given.parameter_type.name)
            expected_types.append(expected.parameter_type.name)

    if parameter_names:
        raise ArtifactParameterTypeMismatchError(
            parameter_names=parameter_names,
            given_types=given_types,
            correct_types=expected_types,
        )
