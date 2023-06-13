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
import pathlib
from typing import Any, Callable, Mapping, Optional, Sequence, Union

import jsonschema.validators

from dioptra.task_engine.error_message import validation_error_to_message
from dioptra.task_engine.issues import IssueSeverity, IssueType, ValidationIssue
from dioptra.task_engine.util import json_path_to_string

_SCHEMA_FILENAME = "experiment_schema.json"


def _experiment_description_path_to_description(  # noqa: C901
    instance_path: Sequence[Union[int, str]]
) -> str:
    """
    Create a nice description of the location in an experiment description
    pointed to by instance_path.  This implementation is crafted specifically
    to the structure of a declarative experiment description.

    Args:
        instance_path: A path, as a sequence of strings/ints.

    Returns:
        A string description
    """

    path_len = len(instance_path)

    message_parts = []
    if path_len == 0:
        message_parts.append("root level of experiment description")

    else:
        if instance_path[0] == "types":
            if path_len == 1:
                message_parts.append("types section")
            else:
                message_parts.append('definition of type "{}"'.format(instance_path[1]))

                if path_len > 2:
                    # Can't slice a Sequence! :-P
                    def_loc = list(instance_path)[2:]
                    message_parts.append("at location " + json_path_to_string(def_loc))

        elif instance_path[0] == "parameters":
            if path_len == 1:
                message_parts.append("global parameters section")
            else:
                message_parts.append("parameter")
                message_parts.append('"{}"'.format(instance_path[1]))

        elif instance_path[0] == "tasks":
            if path_len == 1:
                message_parts.append("tasks section")
            else:
                message_parts.append('task plugin "' + str(instance_path[1]) + '"')
                if path_len > 2:
                    if instance_path[2] == "outputs":
                        message_parts.append("outputs")
                    elif instance_path[2] == "inputs":
                        message_parts.append("inputs")
                    elif instance_path[2] == "plugin":
                        message_parts.append("plugin ID")

        elif instance_path[0] == "graph":
            if path_len == 1:
                message_parts.append("graph section")
            else:
                message_parts.append('step "' + str(instance_path[1]) + '"')
                if len(instance_path) > 2 and instance_path[2] == "dependencies":
                    message_parts.append("dependencies")

    if message_parts:
        description = " ".join(message_parts)
    else:
        # fallbacks if we don't know another way of describing the location
        instance_path_str = json_path_to_string(instance_path)
        description = "experiment description location " + instance_path_str

    return description


def _get_json_schema() -> Union[dict, bool]:  # hypothetical types of schemas
    """
    Read and parse the declarative experiment description JSON-Schema file.

    Returns:
        The schema, as parsed JSON
    """
    # Currently assumes the schema json file and this source file are in the
    # same directory.
    schema_path = pathlib.Path(__file__).with_name(_SCHEMA_FILENAME)

    schema: Union[dict, bool]
    with schema_path.open("r", encoding="utf-8") as fp:
        schema = json.load(fp)

    return schema


def schema_validate_experiment_description(
    experiment_desc: Mapping[str, Any]
) -> list[ValidationIssue]:
    """
    Validate the given declarative experiment description against a JSON-Schema
    schema, and create ValidationIssue objects from any errors found.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """

    schema = _get_json_schema()

    error_messages = schema_validate(
        experiment_desc, schema, _experiment_description_path_to_description
    )

    issues = [
        ValidationIssue(IssueType.SCHEMA, IssueSeverity.ERROR, message)
        for message in error_messages
    ]

    return issues


def schema_validate(
    instance: Any,
    schema: Union[dict, bool],
    location_desc_callback: Optional[Callable[[Sequence[Union[int, str]]], str]] = None,
) -> list[str]:
    """
    Validate the given instance against the given JSON-Schema.

    Args:
        instance: A value to validate
        schema: JSON-Schema as a data structure, e.g. parsed JSON
        location_desc_callback: A callback function used to customize the
            description of the location of errors.  Takes a programmatic "path"
            structure as a sequence of strings/ints, and should return a nice
            one-line string description.  Defaults to a simple generic
            implementation which produces descriptions which aren't very nice.

    Returns:
        A list of error messages; will be empty if validation succeeded
    """
    # Make use of a more complex API to try to produce better schema
    # validation error messages.
    validator_class = jsonschema.validators.validator_for(schema)
    validator = validator_class(schema=schema)

    error_messages = [
        validation_error_to_message(error, schema, location_desc_callback)
        for error in validator.iter_errors(instance)
    ]

    return error_messages
