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
import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from dioptra.sdk.api.swappable_validation import (
    get_swappable_experiment_schema,
    get_swappable_json_schema_resources,
)
from dioptra.sdk.exceptions.base import BaseTaskEngineError
from dioptra.task_engine import util, validation
from dioptra.task_engine.issues import IssueSeverity, IssueType, ValidationIssue


def get_swap_choices(declaration: dict[str, Any]) -> dict[str, Any]:
    """Return invocations without the swap's output interface metadata."""
    return {name: value for name, value in declaration.items() if name != "?outputs"}


def render_swaps_config(
    config: dict[str, Any],
    swaps: dict[str, str],
    raise_unspecified: bool = True,
) -> dict[str, Any]:
    """Render a public configuration using only user-provided names.

    Selected swaps retain their interface and just the selected alias. Unselected
    partial swaps retain all aliases. Registered task definitions are unchanged.
    """
    rendered = deepcopy(config)
    graph = rendered["graph"]
    # Share selection validation with the graph-only introspection helper.
    render_swaps_graph(graph, swaps, raise_unspecified)
    for step in graph.values():
        for swap_name, declaration in step.items():
            if swap_name.startswith("?") and swap_name[1:] in swaps:
                alias = swaps[swap_name[1:]]
                step[swap_name] = {
                    "?outputs": declaration["?outputs"],
                    alias: declaration[alias],
                }
    return rendered


@dataclass
class CompiledSwapsConfig:
    """Internal engine configuration with provenance for public diagnostics.

    Never serialize this configuration into API responses or job artifacts.
    """

    config: dict[str, Any]
    task_names: dict[str, str]

    def public_message(self, message: str) -> str:
        """Translate exact internal identifiers using their recorded provenance."""
        if not self.task_names:
            return message
        pattern = (
            r"(?<![\w-])(?:" + "|".join(map(re.escape, self.task_names)) + r")(?![\w-])"
        )
        return re.sub(pattern, lambda match: self.task_names[match[0]], message)

    @contextmanager
    def public_errors(self) -> Iterator[None]:
        """Translate exceptions before worker logging or API error handling."""
        try:
            yield
        except Exception as error:
            message = self.public_message(str(error))
            if message != str(error):
                raise RuntimeError(message) from None
            raise

    def validate(self) -> list[ValidationIssue]:
        """Validate internally while returning only author-facing diagnostics."""
        with self.public_errors():
            return [
                ValidationIssue(
                    issue.type, issue.severity, self.public_message(issue.message)
                )
                for issue in validation.validate(self.config)
            ]


def _normalize_swap_task(
    task: dict[str, Any], names: list[str], swap_name: str, task_name: str
) -> dict[str, Any]:
    """Copy a task definition and remap its output names positionally."""
    task = deepcopy(task)
    outputs = task.get("outputs", [])
    output_list = [outputs] if isinstance(outputs, dict) else outputs
    if len(names) != len(output_list):
        raise ValueError(
            f"Swap '{swap_name}' task '{task_name}' has {len(output_list)} "
            f"outputs; its interface requires {len(names)}."
        )
    normalized_outputs = [
        {name: next(iter(output.values()))} for name, output in zip(names, output_list)
    ]
    if isinstance(outputs, dict):
        task["outputs"] = normalized_outputs[0]
    elif "outputs" in task:
        task["outputs"] = normalized_outputs
    return task


def compile_swaps_config(config: Mapping[str, Any]) -> CompiledSwapsConfig:
    """Compile a fully selected public configuration for in-memory engine use.

    Each remaining swap must contain exactly one choice. Generated definitions
    are local to each step; original task definitions and the source are retained.
    """
    schema_issues = validation.schema_validate(
        config,
        get_swappable_experiment_schema(),
        resources=get_swappable_json_schema_resources(),
    )
    if schema_issues:
        raise ValueError(
            "Invalid job configuration: " + "; ".join(map(str, schema_issues))
        )
    rendered = deepcopy(dict(config))
    graph = rendered["graph"]
    structure_issues = check_duplicate_swap_names(
        graph
    ) + check_multiple_swaps_per_step(graph)
    if structure_issues:
        raise ValueError("Invalid swaps: " + "; ".join(map(str, structure_issues)))
    swaps = {}
    for name, choices in extract_swaps(graph).items():
        if len(choices) != 1:
            raise ValueError(f"Swap '{name}' requires exactly one selected choice.")
        swaps[name] = choices[0]
    rendered_graph = render_swaps_graph(graph, swaps)
    tasks = rendered["tasks"]
    task_names = {}
    for step_name, step in graph.items():
        for swap_name, declaration in step.items():
            if not swap_name.startswith("?") or swap_name[1:] not in swaps:
                continue
            invocation = get_swap_choices(declaration)[swaps[swap_name[1:]]]
            task_name = util.step_get_plugin_short_name(invocation)
            assert task_name is not None  # The invocation has passed schema validation.
            if task_name not in tasks:
                # Leave unresolved invocations for ordinary engine validation.
                continue
            task = _normalize_swap_task(
                tasks[task_name], declaration["?outputs"], swap_name, task_name
            )

            generated_name = f"{step_name}_{task_name}"
            # Step/task pairs (train_model, score) and (train, model_score)
            # both yield train_model_score; a registered task may also use that
            # name. Append underscores until the local task key is unique.
            while generated_name in tasks:
                generated_name += "_"
            tasks[generated_name] = task
            task_names[generated_name] = (
                f"{task_name} (step '{step_name}', swap '{swap_name}', "
                f"choice '{swaps[swap_name[1:]]}')"
            )
            rendered_step = rendered_graph[step_name]
            if "task" in invocation:
                rendered_step["task"] = generated_name
            else:
                rendered_step[generated_name] = rendered_step.pop(task_name)
    rendered["graph"] = rendered_graph
    return CompiledSwapsConfig(rendered, task_names)


def render_swaps_graph(
    graph: dict[str, Any],
    swaps: dict[str, str],
    raise_unspecified: bool = True,
) -> dict[str, Any]:
    """
    Renders a task graph given a graph containing swaps and dictionary
    specifying the swap choices. Can perform partial renders through setting
    raise_unspecified to False.

    This graph-only helper retains registered task names for introspection
    (for example, required globals and active plugins). Public configurations use
    render_swaps_config; compile_swaps_config prepares them for engine execution.

    Args:
        graph: A dictionary representing the task graph.
        swaps: Mapping of swap names to the selected task alias.
        raise_unspecified: Whether to raise an error for swaps that are present in
            the graph but not supplied in swaps.

    Returns:
        The rendered graph with the provided swaps applied.
    """
    rendered_graph: dict[str, Any] = {}

    used_swaps = set()
    not_found_swaps = set()
    not_found_tasks = set()

    for step, task in graph.items():
        rendered_graph[step] = {}
        for task_name, task_defn in task.items():
            if task_name.startswith("?"):
                swap_name = task_name[1:]

                try:
                    task_alias = swaps[swap_name]
                    used_swaps.add(swap_name)

                    try:
                        swap = get_swap_choices(task_defn)[task_alias]
                        rendered_graph[step].update(swap)
                    except KeyError:
                        not_found_tasks.add(task_alias)
                except KeyError:
                    not_found_swaps.add(swap_name)
                    if not raise_unspecified:
                        # Preserve the original placeholder in the output.
                        rendered_graph[step][task_name] = task_defn

        # The step metadata takes precedence regardless of key order.
        # Merge into a fresh mapping so rendering does not modify a swap option.
        rendered_graph[step].update(
            (name, definition)
            for name, definition in task.items()
            if not name.startswith("?")
        )

    unused_swaps = sorted(swaps.keys() - used_swaps)
    not_found_swaps_list = sorted(not_found_swaps)
    not_found_tasks_list = sorted(not_found_tasks)

    if raise_unspecified and not_found_swaps_list:
        raise ValueError(
            f"Swaps {not_found_swaps_list} needed by graph but not provided."
        )

    if unused_swaps:
        raise ValueError(f"Swaps {unused_swaps} were provided but not used.")

    if not_found_tasks_list:
        raise ValueError(
            f"Tasks {not_found_tasks_list} requested for swaps but were not found."
        )

    return rendered_graph


def validate_swaps_graph(graph):
    # validation checks that can be performed with only the graph portion of the yaml
    issues = []
    issues += validation._find_non_string_keys(graph, "graph")
    issues += validation._check_graph_dependencies({"graph": graph})
    issues += validation._check_step_structure({"graph": graph})
    return issues


def check_swaps_graph_dependencies(graph: dict[str, Any]) -> list[ValidationIssue]:
    """Check the dependency union of a schema-valid graph without rendering choices.

    With unique swap names and at most one swap per step, a cycle in this union
    can be realized by selecting the option contributing each step's cycle edge.
    """
    union_graph = {}
    for step_name, step in graph.items():
        explicit = step.get("dependencies", [])
        dependencies = set([explicit] if isinstance(explicit, str) else explicit)
        invocations = [
            {
                name: value
                for name, value in step.items()
                if name != "dependencies" and not name.startswith("?")
            }
        ]
        for name, aliases in step.items():
            if name.startswith("?"):
                # Inspect each invocation separately: an alias may itself be named task.
                invocations.extend(get_swap_choices(aliases).values())
        for invocation in invocations:
            for reference in util.get_references(invocation):
                referenced_step, _ = util.get_reference_coords(reference)
                if referenced_step in graph:
                    dependencies.add(referenced_step)
        union_graph[step_name] = {"dependencies": sorted(dependencies)}

    try:
        util.get_sorted_steps(union_graph)
    except BaseTaskEngineError as error:
        return [
            ValidationIssue(
                type_=IssueType.SEMANTIC,
                severity=IssueSeverity.ERROR,
                message=str(error),
            )
        ]
    return []


def extract_swaps(task_graph: dict[str, Any]) -> dict[str, list[str]]:
    """Extract swap names and aliases from a task graph."""
    swaps = {}

    for task in task_graph.values():
        for swap_name, aliased_definitions in task.items():
            if swap_name.startswith("?"):
                clean_name = swap_name[1:]
                if clean_name not in swaps:
                    swaps[clean_name] = list(get_swap_choices(aliased_definitions))

    return swaps


def check_duplicate_swap_names(
    task_graph: dict[str, Any],
) -> list[ValidationIssue]:
    """Validate that each swap name appears only once in a task graph."""
    swap_counts: dict[str, int] = {}
    for task in task_graph.values():
        if isinstance(task, dict):
            for key in task:
                if isinstance(key, str) and key.startswith("?"):
                    swap_name = key[1:]
                    swap_counts[swap_name] = swap_counts.get(swap_name, 0) + 1

    return [
        ValidationIssue(
            type_=IssueType.SEMANTIC,
            severity=IssueSeverity.ERROR,
            message=(
                f"Duplicate swap name '{name}' found in task graph "
                f"(appears {count} times)."
            ),
        )
        for name, count in swap_counts.items()
        if count > 1
    ]


def check_multiple_swaps_per_step(
    task_graph: dict[str, Any],
) -> list[ValidationIssue]:
    """Validate that each graph step contains at most one swap."""
    issues = []

    for step_name, task in task_graph.items():
        if not isinstance(task, dict):
            continue

        swap_names = [
            key for key in task if isinstance(key, str) and key.startswith("?")
        ]
        if len(swap_names) > 1:
            issues.append(
                ValidationIssue(
                    type_=IssueType.SEMANTIC,
                    severity=IssueSeverity.ERROR,
                    message=(
                        f"Step '{step_name}' contains multiple swaps "
                        f"({', '.join(swap_names)}). Each step may contain only one swap."
                    ),
                )
            )

    return issues
