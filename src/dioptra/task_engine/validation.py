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
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Union

from dioptra.sdk.exceptions.base import BaseTaskEngineError
from dioptra.task_engine import type_registry, type_validation, types, util
from dioptra.task_engine.error_message import json_path_to_string
from dioptra.task_engine.issues import IssueSeverity, IssueType, ValidationIssue

_SCHEMA_FILENAME = "experiment_schema.json"


def _instance_path_to_description(  # noqa: C901
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


def _schema_validate(experiment_desc: Mapping[str, Any]) -> list[ValidationIssue]:
    """
    Validate the given declarative experiment description against a JSON-Schema
    schema.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """

    schema = _get_json_schema()

    error_messages = util.schema_validate(
        experiment_desc, schema, _instance_path_to_description
    )

    issues = [
        ValidationIssue(IssueType.SCHEMA, IssueSeverity.ERROR, message)
        for message in error_messages
    ]

    return issues


def _find_non_string_keys(mapping: Mapping, key_meaning: str) -> list[ValidationIssue]:
    """
    Look for non-string keys in the given mapping.  Create validation issues
    for any non-string keys found.

    Args:
        mapping: A mapping to check
        key_meaning: Used to describe the keys being checked, in a validation
            issue message.  This way, we can use the same code to check keys
            in several places, but get issue messages which are not generic:
            they describe the role those keys play in the experiment
            description.

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """
    issues = []
    for key in mapping:
        message = None
        if isinstance(key, str):
            if not key or key.isspace():
                message = "{} names must be non-empty/whitespace: {!r}".format(
                    key_meaning, key
                )
        else:
            message = "{} must be strings: {!r}".format(key_meaning, key)

        if message:
            issue = ValidationIssue(IssueType.SEMANTIC, IssueSeverity.ERROR, message)
            issues.append(issue)

    return issues


def _check_string_keys(experiment_desc: Mapping[str, Any]) -> list[ValidationIssue]:
    """
    Ensure certain mappings within the experiment description use only string
    keys.  This check targets certain mappings: type names, global parameter
    names, task short names, graph step names.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """

    types = experiment_desc.get("types", {})
    parameters = experiment_desc.get("parameters", {})
    tasks = experiment_desc["tasks"]
    graph = experiment_desc["graph"]
    issues = []

    issues += _find_non_string_keys(types, "Type names")
    issues += _find_non_string_keys(parameters, "Global parameter names")
    issues += _find_non_string_keys(tasks, "Task short names")
    issues += _find_non_string_keys(graph, "Graph step names")

    return issues


def _check_name_collisions(experiment_desc: Mapping[str, Any]) -> list[ValidationIssue]:
    """
    Check whether any graph step names collide with any parameter names.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """

    param_names = set(experiment_desc.get("parameters", []))
    step_names = set(experiment_desc["graph"])

    collisions = param_names & step_names

    issues = []
    if collisions:
        message = "Some parameters and steps have the same name: " + ", ".join(
            collisions
        )
        issue = ValidationIssue(IssueType.SEMANTIC, IssueSeverity.ERROR, message)
        issues.append(issue)

    return issues


def _check_global_parameter_types(
    experiment_desc: Mapping[str, Any]
) -> list[ValidationIssue]:
    """
    Check whether all global parameter types are valid.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """

    global_parameters = experiment_desc.get("parameters", {})
    type_defs = experiment_desc.get("types", {})
    type_names = type_registry.BUILTIN_TYPES.keys() | type_defs.keys()

    issues = []

    # Can't really use None to mean no default, since that's a valid default!
    no_default = object()

    for param_name, param_def in global_parameters.items():
        if isinstance(param_def, Mapping):
            param_type = param_def.get("type")
            param_default = param_def.get("default", no_default)

            if param_type is not None and param_type not in type_names:
                message = 'In global parameter "{}": undefined type: {}'.format(
                    param_name, param_type
                )

                issue = ValidationIssue(
                    IssueType.SEMANTIC, IssueSeverity.ERROR, message
                )

                issues.append(issue)

            if param_type is None and param_default is no_default:
                # Neither a type nor a default value was given.  This is an
                # invalid situation since there is no way to obtain a parameter
                # type.  I don't think you could create this situation and still
                # be schema-valid, but I want to keep the check anyway.

                message = (
                    'In global parameter "{}": unable to obtain a type:'
                    " neither a type nor default value were given"
                ).format(param_name)

                issue = ValidationIssue(IssueType.TYPE, IssueSeverity.ERROR, message)

                issues.append(issue)

    return issues


def _check_type_definition_type_references(
    experiment_desc: Mapping[str, Any]
) -> list[ValidationIssue]:
    """
    Check for references to undefined types in all type definitions.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """

    type_defs = experiment_desc.get("types", {})
    type_names = type_registry.BUILTIN_TYPES.keys() | type_defs.keys()

    issues = []

    for type_name, type_def in type_defs.items():
        for type_ref in type_registry.get_dependency_types(type_def):
            if type_ref not in type_names:
                message = (
                    'In definition of type "{}": reference to undefined type: {}'
                ).format(type_name, type_ref)

                issue = ValidationIssue(
                    IssueType.SEMANTIC, IssueSeverity.ERROR, message
                )

                issues.append(issue)

    return issues


def _check_type_reference_cycle(
    experiment_desc: Mapping[str, Any]
) -> list[ValidationIssue]:
    """
    Check for a reference cycle among type definitions.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """

    type_defs = experiment_desc.get("types", {})
    issues = []
    message = None

    try:
        type_registry.get_sorted_types(type_defs)

    except BaseTaskEngineError as e:
        # If all references resolve and the description is schema-valid, the
        # only exception that could be thrown is a TypeReferenceCycleError.
        # But I will catch all task engine errors, just in case.
        message = str(e)

    if message:
        issue = ValidationIssue(IssueType.SEMANTIC, IssueSeverity.ERROR, message)
        issues.append(issue)

    return issues


def _check_union_member_duplicates(
    experiment_desc: Mapping[str, Any]
) -> list[ValidationIssue]:
    """
    Check for union type definitions for which there is duplication in the
    membership.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """

    issues = []
    type_defs = experiment_desc.get("types", {})
    type_reg = type_registry.build_type_registry(type_defs)

    for type_name, type_ in type_reg.items():
        if isinstance(type_, types.UnionType):
            # Deduping automatically happens when union types are built.
            # So we can't just check a union type object for dupes; there will
            # never be any.  We must re-create every member type from the
            # definition in order to tell whether there were any duplicates.

            union_type_def = type_defs[type_name]
            member_type_defs = union_type_def["union"]

            dupe_types = set()
            seen_types = set()
            for member_type_def in member_type_defs:
                member_type = type_registry.build_or_get_type(member_type_def, type_reg)

                if member_type in seen_types:
                    dupe_types.add(member_type)
                else:
                    seen_types.add(member_type)

            if dupe_types:
                message = (
                    'In definition of type "{}": duplicate member types'
                    " encountered: {}"
                ).format(type_name, ", ".join(str(t) for t in dupe_types))

                issue = ValidationIssue(
                    IssueType.SEMANTIC, IssueSeverity.WARNING, message
                )

                issues.append(issue)

    return issues


def _check_task_plugin_references(
    experiment_desc: Mapping[str, Any]
) -> list[ValidationIssue]:
    """
    Check whether all task plugin short names refer to known task plugins.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """
    task_defs = experiment_desc["tasks"]
    graph = experiment_desc["graph"]

    issues = []
    for step_name, step_def in graph.items():
        task_plugin_short_name = util.step_get_plugin_short_name(step_def)

        if task_plugin_short_name not in task_defs:
            message = 'In step "{}": unrecognized task plugin: {}'.format(
                step_name, task_plugin_short_name
            )
            issue = ValidationIssue(IssueType.SEMANTIC, IssueSeverity.ERROR, message)
            issues.append(issue)

    return issues


def _check_task_plugin_pyplugs_coords(
    experiment_desc: Mapping[str, Any]
) -> list[ValidationIssue]:
    """
    Check task plugin IDs for validity.  They must at minimum include a module
    name and a function name.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """
    task_defs = experiment_desc["tasks"]

    issues = []
    for task_short_name, task_def in task_defs.items():
        plugin = task_def["plugin"]
        if "." not in plugin:
            message = 'In task "{}": plugin ID requires at least one ".": {}'.format(
                task_short_name, plugin
            )
            issue = ValidationIssue(IssueType.SEMANTIC, IssueSeverity.ERROR, message)
            issues.append(issue)

        plugin_parts = plugin.split(".")
        if any(len(plugin_part) == 0 for plugin_part in plugin_parts):
            message = (
                'In task "{}": all plugin module components must be of'
                " non-zero length: {}"
            ).format(task_short_name, plugin)
            issue = ValidationIssue(IssueType.SEMANTIC, IssueSeverity.ERROR, message)
            issues.append(issue)

    return issues


def _check_task_plugin_io_names(
    experiment_desc: Mapping[str, Any]
) -> list[ValidationIssue]:
    """
    Check task definitions for duplicate input and output names.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """

    task_defs = experiment_desc["tasks"]
    issues = []

    for short_task_name, task_def in task_defs.items():
        inputs = task_def.get("inputs", [])
        names = set()
        repeated_names = set()

        for input_ in inputs:
            name, _ = util.input_def_get_name_type(input_)
            if name in names:
                repeated_names.add(name)
            else:
                names.add(name)

        if repeated_names:
            message = 'In task "{}": some input names are repeated: {}'.format(
                short_task_name, ", ".join(repeated_names)
            )

            issue = ValidationIssue(IssueType.SEMANTIC, IssueSeverity.ERROR, message)

            issues.append(issue)

        outputs = task_def.get("outputs", [])
        repeated_names.clear()
        names.clear()

        if not isinstance(outputs, list):
            outputs = [outputs]

        for output in outputs:
            name = next(iter(output))
            if name in names:
                repeated_names.add(name)
            else:
                names.add(name)

        if repeated_names:
            message = 'In task "{}": some output names are repeated: {}'.format(
                short_task_name, ", ".join(repeated_names)
            )

            issue = ValidationIssue(IssueType.SEMANTIC, IssueSeverity.ERROR, message)

            issues.append(issue)

    return issues


def _check_task_plugin_io_types(
    experiment_desc: Mapping[str, Any]
) -> list[ValidationIssue]:
    """
    Check task definition input and output type names for validity: whether
    they name known types.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """

    type_defs = experiment_desc.get("types", {})
    task_defs = experiment_desc["tasks"]
    issues = []

    type_names = type_registry.BUILTIN_TYPES.keys() | type_defs.keys()

    for short_task_name, task_def in task_defs.items():
        inputs = task_def.get("inputs", [])

        for input_ in inputs:
            name, type_ = util.input_def_get_name_type(input_)
            if type_ not in type_names:
                message = 'In task "{}": input "{}" has undefined type: {}'.format(
                    short_task_name, name, type_
                )

                issue = ValidationIssue(
                    IssueType.SEMANTIC, IssueSeverity.ERROR, message
                )

                issues.append(issue)

        outputs = task_def.get("outputs", [])

        if not isinstance(outputs, list):
            outputs = [outputs]

        for output in outputs:
            name, type_ = next(iter(output.items()))
            if type_ not in type_names:
                message = 'In task "{}": output "{}" has undefined type: {}'.format(
                    short_task_name, name, type_
                )

                issue = ValidationIssue(
                    IssueType.SEMANTIC, IssueSeverity.ERROR, message
                )

                issues.append(issue)

    return issues


def _check_graph_references(  # noqa: C901
    experiment_desc: Mapping[str, Any]
) -> list[ValidationIssue]:
    """
    Scan for references within task invocations, check whether they are legal,
    and whether they refer to recognized parameters, steps, and/or step outputs.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """
    graph = experiment_desc["graph"]
    task_defs = experiment_desc["tasks"]
    params = experiment_desc.get("parameters", {})

    issues = []
    for step_name, step_def in graph.items():
        for ref in util.get_references(step_def):
            message = None

            dot_idx = ref.find(".")
            if dot_idx >= 0:
                ref_name = ref[:dot_idx]
                ref_output = ref[dot_idx + 1 :]
            else:
                ref_name = ref
                ref_output = None

            if ref_name in graph:
                referent_step = graph[ref_name]
                task_plugin_short_name = util.step_get_plugin_short_name(referent_step)
                # unrecognized task plugin short name is a different check.
                # We will disregard that possibility here.
                task_def = task_defs[task_plugin_short_name]
                task_outputs = task_def.get("outputs", [])

                if not isinstance(task_outputs, list):
                    task_outputs = [task_outputs]

                task_output_names = [
                    next(iter(task_output)) for task_output in task_outputs
                ]

                if ref_output is None:
                    if not task_outputs:
                        message = (
                            'In step "{}": reference "{}": referenced'
                            " step produces no output".format(step_name, ref)
                        )
                    elif len(task_outputs) > 1:
                        message = (
                            'In step "{}": reference "{}": an output name must'
                            " be given if the task plugin produces more than"
                            " one output."
                        ).format(step_name, ref)

                elif ref_output not in task_output_names:
                    message = (
                        'In step "{}": reference "{}": unrecognized output: {}'
                    ).format(step_name, ref, ref_output)

            elif ref_name in params:
                if ref_output:
                    message = (
                        'In step "{}": reference "{}": references to parameters'
                        " may not include an output name: {}"
                    ).format(step_name, ref, ref_output)

            else:
                message = 'In step "{}": unresolvable reference: {}'.format(
                    step_name, ref_name
                )

            if message:
                issue = ValidationIssue(
                    IssueType.SEMANTIC, IssueSeverity.ERROR, message
                )
                issues.append(issue)

    return issues


def _check_graph_dependencies(
    experiment_desc: Mapping[str, Any]
) -> list[ValidationIssue]:
    """
    Check explicitly declared dependencies for each step and ensure they refer
    to other steps.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """
    graph = experiment_desc["graph"]

    issues = []
    for step_name, step_def in graph.items():
        deps = step_def.get("dependencies", [])
        if isinstance(deps, str):
            deps = {deps}
        else:
            deps = set(deps)

        unrecognized_deps = deps - graph.keys()

        if unrecognized_deps:
            message = 'In step "{}": unrecognized dependency step(s): {}'.format(
                step_name, ", ".join(unrecognized_deps)
            )
            issue = ValidationIssue(IssueType.SEMANTIC, IssueSeverity.ERROR, message)
            issues.append(issue)

    return issues


def _check_graph_cycle(experiment_desc: Mapping[str, Any]) -> list[ValidationIssue]:
    """
    Check for a cycle in the task graph.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """

    issues = []
    message = None
    try:
        util.get_sorted_steps(experiment_desc["graph"])
    except BaseTaskEngineError as e:
        # If all references resolve and the description is schema-valid, the
        # only exception that could be thrown is a StepReferenceCycleError.
        # But I will catch all task engine errors, just in case.
        message = str(e)

    if message:
        issue = ValidationIssue(IssueType.SEMANTIC, IssueSeverity.ERROR, message)
        issues.append(issue)

    return issues


def _check_names_dots(experiment_desc: Mapping[str, Any]) -> list[ValidationIssue]:
    """
    Check whether any parameter or step names have a dot.  That needs to be
    disallowed because references to these would have the same syntax as a step
    output (<step>.<output>) and be ambiguous or misinterpreted.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """
    parameters = experiment_desc.get("parameters", [])
    graph = experiment_desc["graph"]

    issues = []
    for param_name in parameters:
        # The check for string keys is separate and prerequisite for this
        # check, so we will assume keys are strings here.
        if "." in param_name:
            message = (
                'Parameter name "{}" contains a dot.  References to this'
                " parameter will ambiguously look like step.output"
                " references."
            ).format(param_name)

            issue = ValidationIssue(IssueType.SEMANTIC, IssueSeverity.ERROR, message)

            issues.append(issue)

    for step_name in graph:
        if "." in step_name:
            message = (
                'Step name "{}" contains a dot.  References to this'
                " step will ambiguously look like step.output"
                " references."
            ).format(step_name)

            issue = ValidationIssue(IssueType.SEMANTIC, IssueSeverity.ERROR, message)

            issues.append(issue)

    return issues


def _check_step_structure(experiment_desc: Mapping[str, Any]) -> list[ValidationIssue]:
    """
    Ensure each graph step includes a reference to a task plugin.  This check
    is about the structure of the step, not whether the reference resolves or
    whether the invocation makes sense with respect to the task plugin.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """

    # I tried writing JSON-Schema for this, but I felt it was too complicated
    # (if it had worked at all).  So I wrote some code to check instead.

    graph = experiment_desc["graph"]

    issues = []
    for step_name, step_def in graph.items():
        message = None
        if "task" not in step_def:
            # This is a short-form positional or keyword arg invocation.
            if len(step_def) == 1 and "dependencies" in step_def:
                # As of this writing, this structure does not pass schema
                # validation (i.e. an object with one property which is
                # "dependencies").  So this check won't get a chance to
                # succeed.  I'd like to keep this check here anyway, just in
                # case.
                message = (
                    'In step "{}": illegal task invocation: A'
                    " positional/keyword short form step definition must be an"
                    " object which includes a property whose name is the"
                    " task plugin short name."
                ).format(step_name)

            elif len(step_def) == 2 and "dependencies" not in step_def:
                message = (
                    'In step "{}": illegal task invocation: A'
                    " positional/keyword short form step definition must be an"
                    " object which includes a property whose name is the"
                    " task plugin short name."
                ).format(step_name)

            # Presence of more than two properties is checked in schema.

        if not message:
            # as another safety check if the above checks find no issues,
            # ensure we can get a task plugin short name from the step.
            task_short_name = util.step_get_plugin_short_name(step_def)
            if task_short_name is None:
                message = (
                    'In step "{}": illegal task invocation: unable to'
                    " determine task plugin short name"
                ).format(step_name)

        if message:
            issue = ValidationIssue(IssueType.SEMANTIC, IssueSeverity.ERROR, message)
            issues.append(issue)

    return issues


def _check_task_invocation(experiment_desc: Mapping[str, Any]) -> list[ValidationIssue]:
    """
    Check task invocation args against declared task inputs, with regard
    to name, number, etc (but not type).

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """

    tasks = experiment_desc["tasks"]
    graph = experiment_desc["graph"]

    issues = []

    for step_name, step_def in graph.items():
        task_short_name = util.step_get_plugin_short_name(step_def)
        task_def = tasks[task_short_name]

        task_input_map = util.make_task_input_map(task_def)
        invoc_pos_args, invoc_kwargs = util.step_get_invocation_arg_specs(step_def)

        # step_get_invocation_arg_specs() returns nulls if the step definition
        # is malformed, but we already checked that.  This code does not run
        # unless the step definition is well formed.
        assert invoc_pos_args is not None
        assert invoc_kwargs is not None

        # Sanity check number of positional args given
        num_pos_args = len(invoc_pos_args)
        num_task_inputs = len(task_input_map)
        if num_pos_args > num_task_inputs:
            message = (
                'In step "{}": illegal task invocation: there are more'
                " positional args given than task parameters: {} > {}"
            ).format(step_name, num_pos_args, num_task_inputs)

            issue = ValidationIssue(IssueType.SEMANTIC, IssueSeverity.ERROR, message)

            issues.append(issue)

        # Check for keyword args in the invocation, which do not correspond to
        # defined task parameters
        for invoc_kwarg_name in invoc_kwargs:
            if invoc_kwarg_name not in task_input_map:
                message = (
                    'In step "{}": illegal task invocation: keyword arg does'
                    " not correspond to a task parameter: {}"
                ).format(step_name, invoc_kwarg_name)

                issue = ValidationIssue(
                    IssueType.SEMANTIC, IssueSeverity.ERROR, message
                )

                issues.append(issue)

        # Check for task parameters assigned both positionally and as keyword.
        # Need to zip(invoc_pos_args, task_input_map) to limit the search
        # through task parameters to just those which have positional
        # assignments.  But invoc_pos_args is not otherwise used.  This causes
        # a flake8 error about an unused loop variable.  That error is quieted
        # by adding a leading underscore.
        for idx, (_invoc_pos_arg, task_param_name) in enumerate(
            zip(invoc_pos_args, task_input_map)
        ):
            if task_param_name in invoc_kwargs:
                message = (
                    'In step "{}": illegal task invocation: task parameter'
                    ' "{}" is assigned a value both as a keyword arg and'
                    " positional arg #{}"
                ).format(step_name, task_param_name, idx + 1)

                issue = ValidationIssue(
                    IssueType.SEMANTIC, IssueSeverity.ERROR, message
                )

                issues.append(issue)

        # Check for required parameters which are missing in the invocation
        for idx, (task_param_name, task_param_def) in enumerate(task_input_map.items()):
            required = True
            if "name" in task_param_def:
                required = task_param_def.get("required", True)

            if required:
                present = (
                    len(invoc_pos_args) >= idx + 1
                ) or task_param_name in invoc_kwargs

                if not present:
                    message = (
                        'In step "{}": illegal task invocation: required task'
                        " parameter is not assigned a value: {}"
                    ).format(step_name, task_param_name)

                    issue = ValidationIssue(
                        IssueType.SEMANTIC, IssueSeverity.ERROR, message
                    )

                    issues.append(issue)

    return issues


def _any_errors(issues: Iterable[ValidationIssue]) -> bool:
    """
    Check whether the given iterable of issues includes any of "error"
    severity.

    Args:
        issues: An iterable of validation issues

    Returns:
        True if there are any errors; False if not
    """
    return any(issue.severity is IssueSeverity.ERROR for issue in issues)


def _manually_validate(experiment_desc: Mapping[str, Any]) -> list[ValidationIssue]:
    """
    Do any extra domain-specific handwritten validation we can think of, which
    can't be done (or awkward to do) via JSON-Schema.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """

    issues = []

    string_key_issues = _check_string_keys(experiment_desc)
    issues += string_key_issues

    if not string_key_issues:
        # Obviously the question of dots in names is moot if the names aren't
        # even strings!
        issues += _check_names_dots(experiment_desc)

    issues += _check_task_plugin_io_names(experiment_desc)
    issues += _check_task_plugin_io_types(experiment_desc)
    issues += _check_task_plugin_pyplugs_coords(experiment_desc)

    step_structure_issues = _check_step_structure(experiment_desc)
    issues += step_structure_issues

    name_collision_issues = _check_name_collisions(experiment_desc)
    issues += name_collision_issues

    if not step_structure_issues:
        task_ref_issues = _check_task_plugin_references(experiment_desc)
        issues += task_ref_issues

        # The below checks require correct references (via task short name)
        # to task definitions, so we can find their input requirements.
        if not task_ref_issues:
            issues += _check_task_invocation(experiment_desc)

            # If there were name collisions, we can't properly interpret
            # references.  So we will skip these checks.
            if not name_collision_issues:
                graph_ref_issues = _check_graph_references(experiment_desc)
                graph_ref_issues += _check_graph_dependencies(experiment_desc)
                issues += graph_ref_issues

                # The graph topology is based on references.  If there were
                # reference errors, we don't have sensible graph.  So we aren't
                # able to check the graph for cycles.  So we will skip this
                # check.
                if not graph_ref_issues:
                    issues += _check_graph_cycle(experiment_desc)

    issues += _check_global_parameter_types(experiment_desc)
    issues += _check_type_definition_type_references(experiment_desc)
    issues += _check_type_reference_cycle(experiment_desc)

    # We must have basic things like correct types, tasks, steps, global
    # parameters, and resolvable references therein, before type validation can
    # be expected to succeed.  So maybe make type validation depend on
    # everything above?
    if not _any_errors(issues):
        issues += type_validation.check_types(experiment_desc)

        # This check re-creates the type registry, which can error out if
        # there were type issues detected above (e.g. a type reference cycle).
        # So let's skip the check if there were other errors.
        issues += _check_union_member_duplicates(experiment_desc)

    return issues


def validate(experiment_desc: Mapping[str, Any]) -> list[ValidationIssue]:
    """
    Validate the given declarative experiment description.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        A list of ValidationIssue objects; will be an empty list if the
        experiment description was valid.
    """

    issues = _schema_validate(experiment_desc)

    # If the description is not schema-valid, the basic structure is incorrect,
    # so we won't even try to dig inside it to check anything.
    if not issues:
        issues = _manually_validate(experiment_desc)

    return issues


def is_valid(experiment_desc: Mapping[str, Any]) -> bool:
    """
    Validate the given declarative experiment description and return a simple
    boolean result.  This style is more appropriate in contexts where we only
    care about whether the description is valid or not, and don't need to know
    the reasons.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent

    Returns:
        True if the description is valid; False if not
    """

    issues = validate(experiment_desc)

    # If it's warnings only, let's treat that as valid.
    result = not _any_errors(issues)

    return result
