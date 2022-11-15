import json
import pathlib
from collections.abc import Iterable, Mapping
from typing import Any, Optional, Tuple, Union

import jsonschema
import jsonschema.exceptions

from dioptra.sdk.exceptions.base import BaseTaskEngineError
from dioptra.task_engine import util
from dioptra.task_engine.error_message import validation_errors_to_message

_SCHEMA_FILENAME = "experiment_schema.json"


def _get_json_schema() -> Union[dict, bool]:  # hypothetical types of schemas
    """
    Read and parse the declarative experiment description JSON-Schema file.

    :return: The schema, as parsed JSON
    """
    # Currently assumes the schema json file and this source file are in the
    # same directory.
    schema_path = pathlib.Path(__file__).with_name(_SCHEMA_FILENAME)

    schema: Union[dict, bool]
    with schema_path.open("r", encoding="utf-8") as fp:
        schema = json.load(fp)

    return schema


def _schema_validate(experiment_desc: Mapping[str, Any]) -> Optional[str]:
    """
    Validate the given declarative experiment description against a JSON-Schema
    schema.

    :param experiment_desc: The experiment description, as parsed YAML or
        equivalent
    :return: An error string if the description was invalid; None if it was
        valid
    """

    schema = _get_json_schema()

    # Make use of a more complex API to try to produce better schema
    # validation error messages.
    validator_class = jsonschema.validators.validator_for(schema)
    validator = validator_class(schema=schema)

    error_message = validation_errors_to_message(
        validator.iter_errors(experiment_desc), schema
    ) or None

    return error_message


def _structure_paths_preorder(
    value: Any, parent_path: list[Any] = None
) -> Iterable[Tuple[list[Any], Any]]:
    """
    Does a recursive search through a data structure composed of nested maps
    and iterables (lists), tracking the locations of nested values as it goes.
    The locations (as "paths") are useful in error messages to point users to
    where an error is in a larger data structure.

    Generates path, value 2-tuples, where a "path" is a list of values which
    represents the location of the value, similar to a filesystem path.
    Strings generally indicate keys of objects and ints indicate indices into
    lists.  But if keys are of other types, then non-string path elements could
    also represent non-string keys of objects.  This ambiguity is not too
    important; we just want to represent a location, and I think users will get
    the idea.  We don't need to be able to interpret the list programmatically,
    just create a useful error message.

    The path, value tuples are generated in preorder: parents are generated
    before children.

    :param value: A value to search
    :param parent_path: The path to the given value as a list, or None.  None
        is treated as [], i.e. that 'value' is the root of the data structure,
        so its path is empty.
    """
    if parent_path is None:
        parent_path = []

    yield parent_path, value

    if isinstance(value, Mapping):
        for key, value in value.items():
            yield from _structure_paths_preorder(value, parent_path + [key])

    elif not isinstance(value, str) and util.is_iterable(value):
        for idx, elt in enumerate(value):
            yield from _structure_paths_preorder(elt, parent_path + [idx])


def _structure_paths_to_objects_preorder(
    value: Any
) -> Iterable[Tuple[list[Any], Mapping]]:
    """
    Find mappings in the given value.  The given value is treated as a nested
    data structure composed of mappings and iterables (lists).  The data
    structure is recursively searched to locate the mappings.  Generates
    path, mapping 2-tuples representing the mappings found and their locations
    within the data structure.

    The path, value tuples are generated in preorder: parents are generated
    before children.

    :param value: A value to search
    """
    for path, value in _structure_paths_preorder(value):
        if isinstance(value, Mapping):
            yield path, value


def _check_string_keys(experiment_desc: Mapping[str, Any]) -> list[str]:
    """
    Check the types of keys in the given mapping.  JSON doesn't support other
    than string keys, so JSON-Schema doesn't support checking the types of
    keys.  There would be no point: if someone had tried to use something else,
    the JSON would not have parsed in the first place.  But it is relevant to
    programmatic usage, where people can pass in any dict they want.  So this
    covers a blind spot in JSON-Schema.

    This check ensures all keys in all objects are strings.

    :param experiment_desc: The experiment description, as parsed YAML or
        equivalent
    :return: Non-empty list of error strings if the description was invalid;
        an empty list if it was valid
    """

    errors = []

    for path, obj in _structure_paths_to_objects_preorder(experiment_desc):
        non_string_keys = [
            key for key in obj
            if not isinstance(key, str)
        ]

        if non_string_keys:
            # Would a filesystem path-like syntax be most intuitive for
            # readers?  JSONPath uses "$" for root and "." for subsequent
            # path component separators.  Is that syntax well recognized?
            path_string = "/" + "/".join(str(elt) for elt in path)
            non_string_keys_string = ", ".join(
                str(key) for key in non_string_keys
            )

            errors.append(
                "Found non-string key(s) in object at location {}: {}".format(
                    path_string, non_string_keys_string
                )
            )

    return errors


def _check_name_collisions(experiment_desc: Mapping[str, Any]) -> list[str]:
    """
    Check whether any graph step names collide with any parameter names.

    :param experiment_desc: The experiment description, as parsed YAML or
        equivalent
    :return: Non-empty list of error strings if the description was invalid;
        an empty list if it was valid
    """

    param_names = set(experiment_desc.get("parameters", []))
    step_names = set(experiment_desc["graph"])

    collisions = param_names & step_names

    if collisions:
        errors = [
            "Some parameters and steps have the same name: "
            + ", ".join(collisions)
        ]
    else:
        errors = []

    return errors


def _check_task_plugin_references(
    experiment_desc: Mapping[str, Any]
) -> list[str]:
    """
    Check whether all task plugin short names refer to known task plugins.

    :param experiment_desc: The experiment description, as parsed YAML or
        equivalent
    :return: Non-empty list of error strings if the description was invalid;
        an empty list if it was valid
    """
    task_defs = experiment_desc["tasks"]
    graph = experiment_desc["graph"]

    errors = []
    for step_name, step_def in graph.items():
        error = None
        task_plugin_short_name = util.step_get_plugin_short_name(step_def)

        if task_plugin_short_name not in task_defs:
            error = 'Unrecognized task plugin in step "{}": {}'.format(
                step_name, task_plugin_short_name
            )

        if error:
            errors.append(error)

    return errors


def _check_task_plugin_pyplugs_coords(
    experiment_desc: Mapping[str, Any]
) -> list[str]:
    task_defs = experiment_desc["tasks"]

    errors = []
    for task_short_name, task_def in task_defs.items():
        error = None
        plugin = task_def["plugin"]
        if "." not in plugin:
            error = (
                "Invalid plugin in task '{}': requires at least one '.': {}"
            ).format(
                task_short_name, plugin
            )

        plugin_parts = plugin.split(".")
        if any(
            len(plugin_part) == 0 for plugin_part in plugin_parts
        ):
            error = (
                "Invalid plugin in task '{}': all plugin module components"
                " must be of non-zero length: {}"
            ).format(
                task_short_name, plugin
            )

        if error:
            errors.append(error)

    return errors


def _check_graph_references(experiment_desc: Mapping[str, Any]) -> list[str]:
    """
    Scan for references within task invocations, check whether they are legal,
    and whether they refer to recognized parameters, steps, and/or step outputs.

    :param experiment_desc: The experiment description, as parsed YAML or
        equivalent
    :return: Non-empty list of error strings if the description was invalid;
        an empty list if it was valid
    """
    graph = experiment_desc["graph"]
    task_defs = experiment_desc["tasks"]
    params = experiment_desc.get("parameters", [])

    errors = []
    for step_name, step_def in graph.items():
        for ref in util.get_references(step_def):
            error = None

            dot_idx = ref.find(".")
            if dot_idx >= 0:
                name = ref[:dot_idx]
                output = ref[dot_idx+1:]
            else:
                name = ref
                output = None

            if name in graph:

                referent_step = graph[name]
                task_plugin_short_name = util.step_get_plugin_short_name(referent_step)
                # unrecognized task plugin short name is a different check.
                # We will disregard that possibility here.
                task_def = task_defs.get(task_plugin_short_name, {})
                task_outputs = task_def.get("outputs")

                if output is None:

                    if isinstance(task_outputs, list) \
                            and len(task_outputs) > 1:

                        error = (
                            'In step "{}": reference "{}": an output name must'
                            ' be given if the task plugin produces more than'
                            ' one output.'
                        ).format(
                            step_name, ref
                        )

                elif task_outputs is None or (
                    isinstance(task_outputs, str) and task_outputs != output
                ) or output not in task_outputs:
                    error = (
                        'In step "{}": reference "{}": unrecognized output: {}'
                    ).format(
                        step_name, ref, output
                    )

            elif name in params:
                if output:
                    error = (
                        'In step "{}": reference "{}": references to parameters'
                        ' may not include an output name: {}'
                    ).format(
                        step_name, ref, output
                    )

            else:
                error = 'Unresolvable reference in step "{}": {}'.format(
                    step_name, name
                )

            if error:
                errors.append(error)

    return errors


def _check_graph_dependencies(experiment_desc: Mapping[str, Any]) -> list[str]:
    """
    Check explicitly declared dependencies for each step and ensure they refer
    to other steps.

    :param experiment_desc: The experiment description, as parsed YAML or
        equivalent
    :return: Non-empty list of error strings if the description was invalid;
        an empty list if it was valid
    """
    graph = experiment_desc["graph"]

    errors = []
    for step_name, step_def in graph.items():

        deps = step_def.get("dependencies", [])
        if isinstance(deps, str):
            deps = {deps}
        else:
            deps = set(deps)

        unrecognized_deps = deps - graph.keys()

        if unrecognized_deps:
            error = 'In step "{}": unrecognized dependency step(s): {}'.format(
                step_name, ", ".join(unrecognized_deps)
            )
            errors.append(error)

    return errors


def _check_graph_cycle(experiment_desc: Mapping[str, Any]) -> list[str]:
    """
    Check for a cycle in the task graph.

    :param experiment_desc: The experiment description, as parsed YAML or
        equivalent
    :return: Non-empty list of error strings if the description was invalid;
        an empty list if it was valid
    """

    try:
        util.get_sorted_steps(experiment_desc["graph"])
    except BaseTaskEngineError as e:
        # If all references resolve and the description is schema-valid, the
        # only exception that could be thrown is a StepReferenceCycleError.
        # But I will catch all task engine errors, just in case.
        errors = [str(e)]
    else:
        errors = []

    return errors


def _check_parameter_names_dots(
    experiment_desc: Mapping[str, Any]
) -> list[str]:
    """
    Check whether any parameter names have a dot.  That needs to be disallowed
    because references to the parameter would have the same syntax as a step
    output (<step>.<output>) and be ambiguous or misinterpreted.

    :param experiment_desc: The experiment description, as parsed YAML or
        equivalent
    :return: Non-empty list of error strings if the description was invalid;
        an empty list if it was valid
    """
    parameters = experiment_desc.get("parameters", [])

    errors = []
    for param_name in parameters:

        if "." in param_name:
            error = (
                'Parameter name "{}" contains a dot.  References to this'
                ' parameter will ambiguously look like step.output'
                ' references.'
            ).format(
                param_name
            )

            errors.append(error)

    return errors


def _check_short_form_task_invocation_structure(
    experiment_desc: Mapping[str, Any]
) -> list[str]:
    """
    A requirement for short form task invocations is that if there are two
    properties, one of them must be "dependencies" (the other one would be a
    task plugin short name).  If there is one property, it can't be
    "dependencies".  In other words, a task plugin short name must always be
    one of the properties.  Ensure these requirements are met.

    :param experiment_desc: The experiment description, as parsed YAML or
        equivalent
    :return: Non-empty list of error strings if the description was invalid;
        an empty list if it was valid
    """

    # I tried writing JSON-Schema for this, but I felt it was too complicated
    # (if it had worked at all).  So I wrote some code to check instead.

    graph = experiment_desc["graph"]

    errors = []
    for step_name, step_def in graph.items():
        error = None
        if "task" not in step_def:
            # This is a short-form positional or keyword arg invocation.
            if len(step_def) == 1 and "dependencies" in step_def:
                # As of this writing, this structure does not pass schema
                # validation (i.e. an object with one property which is
                # "dependencies").  So this check won't get a chance to
                # succeed.  I'd like to keep this check here anyway, just in
                # case.
                error = (
                    'Illegal task invocation in step "{}": A'
                    ' positional/keyword short form step definition must be an'
                    ' object which includes a property whose name is the'
                    ' task plugin short name.'
                ).format(
                    step_name
                )

            elif len(step_def) == 2 and "dependencies" not in step_def:
                error = (
                    'Illegal task invocation in step "{}": A'
                    ' positional/keyword short form step definition must be an'
                    ' object which includes a property whose name is the'
                    ' task plugin short name.'
                ).format(
                    step_name
                )

            # Presence of more than two properties is checked in schema.

        if error:
            errors.append(error)

    return errors


def _manually_validate(experiment_desc: Mapping[str, Any]) -> list[str]:
    """
    Do any extra domain-specific handwritten validation we can think of, which
    can't be done (or awkward to do) via JSON-Schema.

    :param experiment_desc: The experiment description, as parsed YAML or
        equivalent
    :return: Non-empty list of error strings if the description was invalid;
        an empty list if it was valid
    """

    errors = []

    errors += _check_task_plugin_pyplugs_coords(experiment_desc)

    string_key_errors = _check_string_keys(experiment_desc)
    errors += string_key_errors

    if not string_key_errors:
        # If some keys aren't strings, the following check for dots in names
        # may fail, since it doesn't make sense on non-string names.
        errors += _check_parameter_names_dots(experiment_desc)

    invocation_errors = _check_short_form_task_invocation_structure(
        experiment_desc
    )
    errors += invocation_errors

    if not invocation_errors:
        # If there are errors in the structure of task plugin invocations, we
        # may not be able to reliably tell which property is a task plugin
        # reference.  So skip this check.
        errors += _check_task_plugin_references(experiment_desc)

    name_collision_errors = _check_name_collisions(experiment_desc)
    errors += name_collision_errors

    if not name_collision_errors:
        # If there were name collisions, we can't properly interpret
        # references.  So we will skip these checks.
        graph_ref_errors = _check_graph_references(experiment_desc)
        graph_ref_errors += _check_graph_dependencies(experiment_desc)
        errors += graph_ref_errors

        if not graph_ref_errors:
            # The graph topology is based on references.  If there were
            # reference errors, we don't have sensible graph.  So we aren't
            # able to check the graph for cycles.  So we will skip this check.
            errors += _check_graph_cycle(experiment_desc)

    return errors


def validate(experiment_desc: Mapping[str, Any]) -> list[str]:
    """
    Validate the given declarative experiment description.

    :param experiment_desc: The experiment description, as parsed YAML or
        equivalent
    :return: Non-empty list of error strings if the description was invalid;
        an empty list if it was valid
    """

    schema_result = _schema_validate(experiment_desc)

    # If the description is not schema-valid, the basic structure is incorrect,
    # so we won't even try to dig inside it to check anything.
    if schema_result:
        result = [schema_result]

    else:
        result = _manually_validate(experiment_desc)

    return result


def is_valid(experiment_desc: Mapping[str, Any]) -> bool:
    """
    Validate the given declarative experiment description and return a simple
    boolean result.  This style is more appropriate in contexts where we only
    care about whether the description is valid or not, and don't need to know
    the reasons.

    :param experiment_desc: The experiment description, as parsed YAML or
        equivalent
    :return: True if the description is valid; False if not
    """

    errors = validate(experiment_desc)

    # validate() returns a list of error strings, so an empty list (falsey)
    # means the description was valid.
    return not bool(errors)
