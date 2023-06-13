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
"""
Complete a declarative experiment description with data from task plugin and
type REST API endpoints.
"""
import enum
import logging
from collections.abc import Mapping, MutableMapping, MutableSequence, MutableSet
from typing import Any, Optional

try:
    from scripts.client import DioptraClient
except ImportError:
    # The scripts.client module is not part of the source tree.  This hack
    # at least allows unit tests to pass without needing the real module.
    class DioptraClient:
        pass


from dioptra.task_engine import schema_validation, type_registry, util
from dioptra.task_engine.issues import IssueSeverity, IssueType, ValidationIssue


class CompletionPolicy(enum.Enum):
    # Do no completion.  Kinda silly, since you would not invoke this module
    # at all in this case, right?  But here for completeness.
    NONE = enum.auto()

    # Fill in the "gaps".  Only query a webservice for missing definitions.
    ENRICH = enum.auto()

    # Override all definitions with server definitions where possible.  All
    # definitions will need to be looked up to determine whether there is an
    # overriding definition.
    OVERRIDE = enum.auto()

    # Same as OVERRIDE, plus local definitions are removed.  This forces only
    # server definitions to be used.
    STRICT = enum.auto()


def _get_logger() -> logging.Logger:
    """
    Get a logger to use for functions in this module.

    Returns:
        The logger
    """
    return logging.getLogger(__name__)


def _type_name_from_param_def(param_def: Any) -> Optional[str]:
    """
    Get the type name from a global parameter definition, if any.  Legal
    parameter definitions need not name a type, if they give a default value
    from which a type may be inferred.

    Args:
        param_def: A global parameter definition

    Returns:
        A type name, or None if the parameter definition did not name a type.
    """

    type_name = None

    if isinstance(param_def, Mapping):
        type_name = param_def.get("type")

    return type_name


def _complete_tasks(
    experiment_desc: Mapping[str, Any],
    dioptra_client: DioptraClient,
    policy: CompletionPolicy,
    allow_custom_task_plugins: bool,
) -> list[ValidationIssue]:
    """
    Ensure all task definitions required due to references from graph steps,
    are present, querying the webservice if necessary.  Remove unused task
    definitions.

    Args:
        experiment_desc: An experiment description
        dioptra_client: A DioptraClient instance, used for interaction with
            the Dioptra webservice
        policy: A policy value describing how/when definitions ought to be
            looked up in the webservice.
        allow_custom_task_plugins: A boolean flag which determines whether
            definitions of custom task plugins are allowed in the experiment
            description.

    Returns:
        A list of validation issue objects, which may be empty if there were no
        issues found.
    """
    log = _get_logger()

    issues = []

    tasks = experiment_desc["tasks"]
    graph = experiment_desc["graph"]
    visited_task_plugin_ids = set()

    for step_def in graph.values():
        task_plugin_id = util.step_get_plugin_short_name(step_def)

        # If task_plugin_id is None, the step definition is malformed.  We do
        # not handle that error here.
        if task_plugin_id is not None:
            if task_plugin_id not in visited_task_plugin_ids:
                visited_task_plugin_ids.add(task_plugin_id)

                if task_plugin_id not in tasks or policy is CompletionPolicy.OVERRIDE:
                    log.info("Searching for task: %s", task_plugin_id)
                    task_def = dioptra_client.get_task_definition(
                        task_plugin_id, allow_custom_task_plugins
                    )

                    if task_def:
                        tasks[task_plugin_id] = task_def

                    elif task_plugin_id not in tasks:
                        message = "task plugin not registered: " + task_plugin_id
                        issue = ValidationIssue(
                            IssueType.ENTITY, IssueSeverity.ERROR, message
                        )
                        issues.append(issue)

    unused_task_plugin_ids = tasks.keys() - visited_task_plugin_ids
    if unused_task_plugin_ids:
        log.warning(
            "Removing unused task definitions: %s", ", ".join(unused_task_plugin_ids)
        )

        for task_plugin_id in unused_task_plugin_ids:
            del tasks[task_plugin_id]

    return issues


def _complete_type(
    type_defs: MutableMapping[str, Any],
    type_name: str,
    dioptra_client: DioptraClient,
    policy: CompletionPolicy,
    visited_type_names: Optional[MutableSet[str]] = None,
    type_name_stack: Optional[MutableSequence[str]] = None,
) -> list[ValidationIssue]:
    """
    Check for a type definition with the given name, querying it from the
    Dioptra REST API if necessary according to policy, and recursively do the
    same for all dependency types, sub-dependencies, etc.  Update the given
    set of type definitions accordingly.  Built-in types are ignored.

    Args:
        type_defs: A set of type definitions, as a mapping from type name to
            definition.  This is updated in place with new definitions as
            necessary.
        type_name: A type name to validate
        dioptra_client: A DioptraClient instance, used for interaction with
            the Dioptra webservice
        policy: A policy value describing how/when definitions ought to be
            looked up in the webservice.
        visited_type_names: A set of type names, used to avoid validating the
            same types more than once, and to track which types are in use
            and which are not.  This is updated in place, as types are
            validated.  If None, a new empty set is created, which means no
            types are treated as having been previously validated.
        type_name_stack: Tracks chains of type references through the recursive
            calls, useful in issue messages to help users understand why a
            particular type is being looked up.  If None, start a new stack.

    Returns:
        A list of validation issue objects, which may be empty if there were no
        issues found.
    """
    log = _get_logger()

    if type_name_stack is None:
        type_name_stack = []

    if visited_type_names is None:
        visited_type_names = set()

    issues = []

    if (
        type_name not in visited_type_names
        and type_name not in type_registry.BUILTIN_TYPES
    ):
        type_name_stack.append(type_name)
        visited_type_names.add(type_name)

        if type_name not in type_defs or policy is CompletionPolicy.OVERRIDE:
            log.info("Searching for type: %s", type_name)
            type_def = dioptra_client.get_type_definition(type_name)

            if type_def:
                if type_def is dioptra_client.NULL_TYPE_DEFINITION:
                    type_def = None

                type_defs[type_name] = type_def

            elif type_name not in type_defs:
                message = "{}type not registered: {}".format(
                    ("via types " + " > ".join(type_name_stack) + ", ")
                    if len(type_name_stack) > 1
                    else "",
                    type_name,
                )
                issue = ValidationIssue(IssueType.ENTITY, IssueSeverity.ERROR, message)
                issues.append(issue)

        # We must ensure all dependency types are present, even if the type
        # definition we needed was already present.
        if type_name in type_defs:
            for dep_type_name in type_registry.get_dependency_types(
                type_defs[type_name]
            ):
                issues += _complete_type(
                    type_defs,
                    dep_type_name,
                    dioptra_client,
                    policy,
                    visited_type_names,
                    type_name_stack,
                )

        type_name_stack.pop()

    return issues


def _complete_types_from_global_parameters(
    experiment_desc: Mapping[str, Any],
    dioptra_client: DioptraClient,
    policy: CompletionPolicy,
    visited_type_names: MutableSet[str],
) -> list[ValidationIssue]:
    """
    Ensure all type definitions required due to references from global
    parameter definitions, are present.  This includes all dependency types,
    sub-dependency types, etc.  Type definitions are recursively scanned for
    references to other types.

    Args:
        experiment_desc: An experiment description
        dioptra_client: A DioptraClient instance, used for interaction with
            the Dioptra webservice
        policy: A policy value describing how/when definitions ought to be
            looked up in the webservice.
        visited_type_names: A set of type names, used to avoid validating the
            same types more than once, and to track which types are in use
            and which are not.  This is updated in place, as types are
            validated.  If None, a new empty set is created, which means no
            types are treated as having been previously validated.

    Returns:
        A list of validation issue objects, which may be empty if there were no
        issues found.
    """

    issues = []
    types = experiment_desc["types"]
    parameters = experiment_desc.get("parameters", {})

    for param_name, param_def in parameters.items():
        type_name = _type_name_from_param_def(param_def)

        if type_name is not None:
            param_issues = _complete_type(
                types, type_name, dioptra_client, policy, visited_type_names
            )

            for param_issue in param_issues:
                param_issue.message = 'Via parameter "{}": {}'.format(
                    param_name, param_issue.message
                )
            issues += param_issues

    return issues


def _complete_types_from_tasks(
    experiment_desc: Mapping[str, Any],
    dioptra_client: DioptraClient,
    policy: CompletionPolicy,
    visited_type_names: Optional[MutableSet[str]] = None,
) -> list[ValidationIssue]:
    """
    Ensure all type definitions required due to references from task inputs and
    outputs, are present.  This includes all dependency types, sub-dependency
    types, etc.  Type definitions are recursively scanned for references to
    other types.

    Args:
        experiment_desc: An experiment description
        dioptra_client: A DioptraClient instance, used for interaction with
            the Dioptra webservice
        policy: A policy value describing how/when definitions ought to be
            looked up in the webservice.
        visited_type_names: A set of type names, used to avoid validating the
            same types more than once, and to track which types are in use
            and which are not.  This is updated in place, as types are
            validated.  If None, a new empty set is created, which means no
            types are treated as having been previously validated.

    Returns:
        A list of validation issue objects, which may be empty if there were no
        issues found.
    """

    issues = []
    tasks = experiment_desc["tasks"]
    types = experiment_desc["types"]

    if visited_type_names is None:
        visited_type_names = set()

    for task_plugin_name, task_def in tasks.items():
        # Complete types from task inputs
        for in_def in task_def.get("inputs", []):
            in_name, in_type_name = util.input_def_get_name_type(in_def)

            task_issues = _complete_type(
                types, in_type_name, dioptra_client, policy, visited_type_names
            )

            for task_issue in task_issues:
                task_issue.message = 'Via task "{}", input "{}": {}'.format(
                    task_plugin_name, in_name, task_issue.message
                )
            issues += task_issues

        # Complete types from task outputs:
        outputs = task_def.get("outputs", [])
        if isinstance(outputs, Mapping):
            outputs = [outputs]

        for output in outputs:
            out_name, out_type_name = next(iter(output.items()))

            task_issues = _complete_type(
                types, out_type_name, dioptra_client, policy, visited_type_names
            )

            for task_issue in task_issues:
                task_issue.message = 'Via task "{}", output "{}": {}'.format(
                    task_plugin_name, out_name, task_issue.message
                )
            issues += task_issues

    return issues


def _complete_types(
    experiment_desc: Mapping[str, Any],
    dioptra_client: DioptraClient,
    policy: CompletionPolicy,
) -> list[ValidationIssue]:
    """
    Ensure all type definitions required due to references from task and
    global parameter definitions, are present.  Remove unused type definitions.

    experiment_desc: An experiment description
    dioptra_client: A DioptraClient instance, used for interaction with
        the Dioptra webservice
    policy: A policy value describing how/when definitions ought to be
        looked up in the webservice.

    Returns:
        A list of validation issue objects, which may be empty if there were no
        issues found.
    """

    log = _get_logger()
    visited_type_names: MutableSet[str] = set()

    issues = _complete_types_from_tasks(
        experiment_desc, dioptra_client, policy, visited_type_names
    )

    issues += _complete_types_from_global_parameters(
        experiment_desc, dioptra_client, policy, visited_type_names
    )

    type_defs = experiment_desc["types"]
    unused_type_names = type_defs.keys() - visited_type_names
    if unused_type_names:
        log.warning(
            "Removing unused type definitions: %s", ", ".join(unused_type_names)
        )

        for type_name in unused_type_names:
            del type_defs[type_name]

    return issues


def complete(
    experiment_desc: MutableMapping[str, Any],
    dioptra_client: DioptraClient,
    policy: CompletionPolicy = CompletionPolicy.STRICT,
    allow_custom_task_plugins: bool = True,
) -> list[ValidationIssue]:
    """
    "Complete" the given experiment description by looking up definitions
    using the webservice according to a policy.  This will add/override
    definitions in the description as necessary.  If successful, the result is
    a self-contained experiment description, i.e. with no broken references.
    Everything is present which is needed to further validate and run the
    experiment.  Unused task/type definitions are also removed.

    Args:
        experiment_desc: An experiment description
        dioptra_client: A DioptraClient instance, used for interaction with
            the Dioptra webservice
        policy: A policy value describing how/when definitions ought to be
            looked up in the webservice.
        allow_custom_task_plugins: A boolean flag which determines whether
            definitions of custom task plugins are allowed in the experiment
            description.

    Returns:
        A list of validation issue objects, which may be empty if there were no
        issues found.
    """

    issues = []

    if policy is not CompletionPolicy.NONE:
        # Need to schema-validate first.  Subsequent code relies on valid
        # structure.
        issues += schema_validation.schema_validate_experiment_description(
            experiment_desc
        )

        if not issues:
            types = experiment_desc.setdefault("types", {})
            tasks = experiment_desc.setdefault("tasks", {})

            if policy is CompletionPolicy.STRICT:
                # In strict mode, we must not use user's task/type definitions.
                types.clear()
                tasks.clear()
                # After having cleared the types/tasks, the override policy is
                # equivalent to strict.  In fact, the enrich policy would be
                # too... but this allows us to simplify other code such that it
                # doesn't have to have special handling for the "strict" policy.
                policy = CompletionPolicy.OVERRIDE

            # Order is important here: which type definitions are necessary
            # depends on which task definitions are present (since task
            # definitions can refer to types).  So we need to establish the set
            # of task definitions first.
            issues += _complete_tasks(
                experiment_desc, dioptra_client, policy, allow_custom_task_plugins
            )
            issues += _complete_types(experiment_desc, dioptra_client, policy)

            # if the "types" and/or "tasks" sections are empty at this point,
            # perhaps they should be deleted from the description?
            if not types:
                del experiment_desc["types"]

            if not tasks:
                # But in a valid (and complete, self-contained) experiment
                # description, there *must* be at least one task!  So this
                # should not happen in a valid description.
                del experiment_desc["tasks"]

    return issues
