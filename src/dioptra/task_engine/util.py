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
import graphlib
from collections.abc import Callable, Container, Iterator, Mapping, Sequence
from typing import Any, Optional, Union

import jsonschema.validators

from dioptra.sdk.exceptions.task_engine import (
    StepNotFoundError,
    StepReferenceCycleError,
)
from dioptra.task_engine.error_message import validation_error_to_message


def is_iterable(value: Any) -> bool:
    """
    Determine whether the given value is iterable.  Works by attempting to
    get an iterator from it.

    Args:
        value: The value to check

    Returns:
        True if the value is iterable; False if not
    """
    try:
        iter(value)
    except TypeError:
        result = False
    else:
        result = True

    return result


def schema_validate(
    instance: Any,
    schema: Union[dict[str, Any], bool],
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


def step_get_plugin_short_name(step: Mapping[str, Any]) -> Optional[str]:
    """
    Get the plugin short name from a step description.  There is a bit of
    complexity to this, since step descriptions can take different forms, and
    some properties can have special meanings and should not be mistaken for a
    task plugin short name.

    Args:
        step: A step description, as a mapping

    Returns:
        A task plugin short name, or None if one was not found
    """
    plugin_name = None
    if "task" in step:
        plugin_name = step["task"]
    else:
        for key in step:
            # Top-level "dependencies" key has a special meaning; ignore that.
            if key != "dependencies":
                plugin_name = key
                break

    return plugin_name


def step_get_invocation_arg_specs(
    step_def: Mapping[str, Any]
) -> Union[tuple[list[Any], Mapping[str, Any]], tuple[None, None]]:
    """
    Get invocation positional and keyword arg specs from the given step.  This
    just extracts and returns the specs as they are and doesn't resolve any
    references.

    :param step_def: A task graph step definition
    :return: A 2-tuple consisting of positional args and keyword args.
        Positional args are returned as a list of values; keyword args are
        returned as a mapping from name to value.  Either collection may be
        empty.  If no arg specs could be found in the step definition, (None,
        None) is returned.  This is different from empty arg specs.  If no arg
        specs are found, that means the step definition is malformed.
    """

    task_plugin_short_name = step_get_plugin_short_name(step_def)
    if task_plugin_short_name is None:
        pos_arg_specs = kwarg_specs = None

    else:
        if "task" in step_def:
            # Mixed step definition
            pos_arg_specs = step_def.get("args", [])
            kwarg_specs = step_def.get("kwargs", {})

        else:
            # Positional or keyword step definition
            arg_specs = step_def[task_plugin_short_name]

            if isinstance(arg_specs, dict):
                # Must be keyword
                pos_arg_specs = []
                kwarg_specs = arg_specs

            else:
                # Must be positional
                pos_arg_specs = arg_specs
                kwarg_specs = {}

        if not isinstance(pos_arg_specs, list):
            # ensure positional args are in a list
            pos_arg_specs = [pos_arg_specs]

    return pos_arg_specs, kwarg_specs


def is_reference(value: str) -> bool:
    """
    Determine whether the given string, as may be found in a task invocation
    specification, is syntactically a reference.  References begin with a
    dollar sign and are followed by some non-dollar-sign characters, e.g.
    "$foo".  A dollar sign may be escaped by doubling it.  So "$$foo" is not a
    reference, but just means the string "$foo".  If there are no
    non-dollar-sign characters, it is not a reference, e.g. "$", "$$", etc.
    This function does not try to actually resolve the reference, so if the
    value is a reference, this function does not guarantee it is valid.

    Args:
        value: The string to check

    Returns:
        True if the given string is a reference; False if not
    """

    return value != "$" and value.startswith("$") and not value.startswith("$$")


def get_references(input_: Any) -> Iterator[str]:
    """
    Search for references within a task invocation specification, and generate
    the names.  This just makes the reference determination syntactically, and
    doesn't attempt to resolve any reference.

    Args:
        input_: The arg spec structure to search for references

    Yields:
        References, as strings without the leading "$"
    """

    if isinstance(input_, str):
        if is_reference(input_):
            yield input_[1:]  # drop the leading "$"

    elif isinstance(input_, dict):
        if "task" in input_:
            args = input_.get("args")
            kwargs = input_.get("kwargs")
            if args:
                yield from get_references(args)
            if kwargs:
                yield from get_references(kwargs.values())
        else:
            yield from get_references(input_.values())

    elif is_iterable(input_):
        for elt in input_:
            yield from get_references(elt)


def _get_step_references(input_: Any, step_names: Container[str]) -> Iterator[str]:
    """
    Generate step names from references in the input which refer to steps.

    Args:
        input_: The arg spec structure to search for references to steps
        step_names: A container with all of the step names.  This allows us
            to recognize a step name when we see one.

    Yields:
        Referenced step names
    """
    # Note: erroneous references will not be caught here (i.e. those which
    # don't refer to either a step name or a global parameter).  Those errors
    # will be caught later, when we actually need to resolve the references.
    for ref_name in get_references(input_):
        dot_idx = ref_name.find(".")
        if dot_idx >= 0:
            step_name = ref_name[:dot_idx]
        else:
            step_name = ref_name

        if step_name in step_names:
            yield step_name


def get_sorted_steps(step_graph: Mapping[str, Any]) -> list[str]:
    """
    Find a topological sorted list of step names for the given graph.

    Args:
        step_graph: Step definitions, as a mapping from step name to step
            definition.

    Returns:
        A list of step names
    """
    topo_sorter: graphlib.TopologicalSorter = graphlib.TopologicalSorter()

    for step_name, step_def in step_graph.items():
        topo_sorter.add(step_name)

        for dep_step_name in _get_step_references(step_def, step_graph.keys()):
            if dep_step_name in step_graph:
                topo_sorter.add(step_name, dep_step_name)
            else:
                raise StepNotFoundError(dep_step_name, step_name)

        explicit_deps = step_def.get("dependencies", [])
        if isinstance(explicit_deps, str):
            explicit_deps = [explicit_deps]

        for dep_step_name in explicit_deps:
            if dep_step_name in step_graph:
                topo_sorter.add(step_name, dep_step_name)
            else:
                raise StepNotFoundError(dep_step_name, step_name)

    try:
        sorted_steps = list(topo_sorter.static_order())
    except graphlib.CycleError as e:
        raise StepReferenceCycleError(e.args[1]) from e

    return sorted_steps


def input_def_get_name_type(in_def: Mapping[str, Any]) -> tuple[str, str]:
    """
    Get a parameter name and type from a task input parameter definition.

    :param in_def: A task input definition
    :return: A (name, type) 2-tuple
    """
    if "name" in in_def:
        in_name = in_def["name"]
        in_type = in_def["type"]

    else:
        in_name, in_type = next(iter(in_def.items()))

    return in_name, in_type


def make_task_input_map(task_def: Mapping[str, Any]) -> Mapping[str, Any]:
    """
    Make a mapping from task input parameter name to parameter definition,
    from the given task definition.  Since python dicts remember insertion
    order (as iteration order), if we are deliberate about insertion order, we
    can use the mapping for both positional and keyword arg validation: we can
    be sure that the Nth positional task invocation parameter can be matched to
    the Nth map item in iteration order.

    :param task_def: A task definition
    :return: A mapping from task input parameter name to definition
    """
    task_inputs = task_def.get("inputs", [])

    if not isinstance(task_inputs, list):
        task_inputs = [task_inputs]

    task_inputs_map = {}
    for task_input in task_inputs:
        input_name, _ = input_def_get_name_type(task_input)

        # Assume all these names are unique.
        task_inputs_map[input_name] = task_input

    return task_inputs_map
