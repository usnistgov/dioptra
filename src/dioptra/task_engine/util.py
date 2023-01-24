import itertools
from collections.abc import Container, Iterator, Mapping, MutableSequence, MutableSet
from typing import Any, Callable, Optional, Sequence, Union

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

    :param value: The value to check
    :return: True if the value is iterable; False if not
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
    schema: Union[dict, bool],
    location_desc_callback: Optional[Callable[[Sequence[Union[int, str]]], str]] = None,
) -> list[str]:
    """
    Validate the given instance against the given JSON-Schema.

    :param instance: A value to validate
    :param schema: JSON-Schema as a data structure, e.g. parsed JSON
    :param location_desc_callback: A callback function used to customize the
        description of the location of errors.  Takes a programmatic "path"
        structure as a sequence of strings/ints, and should return a nice
        one-line string description.  Defaults to a simple generic
        implementation which produces descriptions which aren't very nice.
    :return: A list of error messages; will be empty if validation succeeded
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

    :param step: A step description, as a mapping
    :return: A task plugin short name, or None if one was not found
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

    :param value: The string to check
    :return: True if the given string is a reference; False if not
    """

    return value != "$" and value.startswith("$") and not value.startswith("$$")


def get_references(input_: Any) -> Iterator[str]:
    """
    Search for references within a task invocation specification, and generate
    the names.  This just makes the reference determination syntactically, and
    doesn't attempt to resolve any reference.

    :param input_: The arg spec structure to search for references
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

    :param input_: The arg spec structure to search for references to steps
    :param step_names: A container with all of the step names.  This allows us
        to recognize a step name when we see one.
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


def _step_dfs(
    step_graph: Mapping[str, Any],
    curr_step_name: str,
    visited_steps: MutableSet[str],
    search_path: MutableSequence[str],
) -> list[str]:
    """
    Perform depth-first search through the task graph, to produce a total order
    over step names which is compatible with the steps' dependencies.

    :param step_graph: The task graph data from the experiment description.
        This maps step names to task invocations.
    :param curr_step_name: The start node of the DFS (since the algorithm is
        recursive, this actually tracks the "current node" through the
        recursive calls).
    :param visited_steps: Set containing steps which have already been visited,
        to avoid visiting any step more than once.  Steps are added to this
        set as the search proceeds.
    :param search_path: A list (acting as a stack) of step names on the current
        search path, used to detect cycles.  Steps are pushed and popped from
        this list as the search proceeds.
    :return: A list of the steps reachable from the start, in topological
        sorted order
    """

    if curr_step_name not in step_graph:
        raise StepNotFoundError(curr_step_name)

    if curr_step_name in search_path:
        cycle_start_idx = search_path.index(curr_step_name)
        cycle = search_path[cycle_start_idx:]
        cycle.append(curr_step_name)
        raise StepReferenceCycleError(cycle)

    sorted_steps = []

    if curr_step_name not in visited_steps:

        curr_step = step_graph[curr_step_name]
        visited_steps.add(curr_step_name)
        search_path.append(curr_step_name)

        # All dependencies include those implied by declared task inputs,
        # and those explicitly listed as dependencies (via the "dependencies"
        # key).

        implicit_deps = _get_step_references(curr_step, step_graph.keys())

        explicit_deps = curr_step.get("dependencies", [])
        if isinstance(explicit_deps, str):
            explicit_deps = [explicit_deps]

        all_dependencies = itertools.chain(implicit_deps, explicit_deps)

        for next_step_name in all_dependencies:
            sub_sorted = _step_dfs(
                step_graph, next_step_name, visited_steps, search_path
            )
            sorted_steps.extend(sub_sorted)

        search_path.pop()
        sorted_steps.append(curr_step_name)

    return sorted_steps


def get_sorted_steps(step_graph: Mapping[str, Any]) -> list[str]:
    """
    Topological sorts the step graph to obtain a sequential execution order.

    :param step_graph: The task graph data from the experiment description.
        This maps step names to task invocations.
    :return: A list of all step names in the graph, in topological sorted order
        according to their dependencies
    """

    sorted_steps = []
    visited_steps: MutableSet[str] = set()
    for step in step_graph:
        sub_sorted = _step_dfs(step_graph, step, visited_steps, [])
        sorted_steps.extend(sub_sorted)

    return sorted_steps
