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
from typing import Any

from dioptra.task_engine import validation


def render_swaps_graph(
    swaps: dict[str, str],
    raise_unspecified: bool = True,
) -> dict[str, Any]:
    """
    Renders a task graph given a graph containing swaps and dictionary
    specifying the swap choices. Can perform partial renders through setting
    raise_unspecified to False.

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
                        swap = task_defn[task_alias]
                        rendered_graph[step] = swap
                    except KeyError:
                        not_found_tasks.add(task_alias)
                except KeyError:
                    not_found_swaps.add(swap_name)
                    if not raise_unspecified:
                        # Preserve the original placeholder in the output.
                        rendered_graph[step][task_name] = task_defn
            else:
                rendered_graph[step][task_name] = task_defn

    unused_swaps = swaps.keys() - used_swaps

    if raise_unspecified and len(not_found_swaps) > 0:
        raise Exception(f"Swaps {not_found_swaps} needed by graph but not provided.")

    if len(unused_swaps) > 0:
        raise Exception(f"Swaps {unused_swaps} were provided but not used.")

    if len(not_found_tasks) > 0:
        raise Exception(
            f"Tasks {not_found_tasks} requested for swaps but were not found."
        )

    return rendered_graph


def validate_swaps_graph(graph):
    # validation checks that can be performed with only the graph portion of the yaml
    issues = []
    issues += validation._find_non_string_keys(graph, "graph")
    issues += validation._check_graph_dependencies({"graph": graph})
    issues += validation._check_step_structure({"graph": graph})
    return issues
