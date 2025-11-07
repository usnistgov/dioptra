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
    graph: dict[str, Any], 
    swaps: dict[str, str]
) -> dict[str, Any]:
    """
    Requests signature analysis for the functions in an annotated python file.

    Args:
        graph: A dictionary object representing a task graph.
        swaps: A dictionary mapping swap names to the selected task.

    Returns:
        The rendered graph using the selected swaps.

    """
    rendered_graph = {}

    used_swaps = set()
    not_found_swaps = set()
    not_found_tasks = set()

    for step, task in graph.items():
        if step.startswith("_"):
            continue

        rendered_graph[step] = {}
        for task_name, task_defn in task.items():
            if task_name.startswith("?"):
                task_name = task_name[1:]

                try:
                    swapped_name = swaps[task_name]
                    used_swaps.add(task_name)
                    
                    try:
                        swap = task_defn[swapped_name]
                        rendered_graph[step][swapped_name] = swap
                    except KeyError:
                        not_found_tasks.add(swapped_name)
                except KeyError:
                    not_found_swaps.add(task_name)
            else:
                rendered_graph[step][task_name] = graph[step][task_name]

    print(swaps.keys(), used_swaps, flush=True)
    unused_swaps = swaps.keys() - used_swaps

    if len(not_found_swaps) > 0:
        raise Exception(f"Swaps {not_found_swaps} needed by graph but not provided.")

    if len(unused_swaps) > 0:
        raise Exception(f"Swaps {unused_swaps} were provided but not used.")

    if len(not_found_tasks) > 0:
        raise Exception(f"Tasks {not_found_tasks} requested for swaps but were not found.")

    return rendered_graph


def validate_swaps_graph(graph):
    # validation checks that can be performed with only the graph portion of the yaml
    issues = []
    issues += validation._find_non_string_keys(graph, "graph")
    issues += validation._check_graph_dependencies({"graph": graph})
    issues += validation._check_step_structure({"graph": graph})
    return issues
