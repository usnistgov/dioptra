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
import yaml
from pprint import pprint
from dioptra.task_engine import validation

def render(graph, swaps):
    rendered_graph = {}
    for step, task in graph.items():
        if step.startswith("_"):
            continue

        rendered_graph[step] = {}
        for task_name, task_defn in task.items():
            if task_name.startswith("?"):
                task_name = swaps[task_name[1:]]  # could raise swap not specified error
                swap = task_defn[task_name]
                rendered_graph[step][task_name] = swap
            else:
                rendered_graph[step][task_name] = graph[step][task_name]

    return rendered_graph

def validate(graph):
    # validation checks that can be performed with only the graph portion of the yaml
    issues = []
    issues += validation._find_non_string_keys(graph, "graph")
    issues += validation._check_graph_dependencies({"graph": graph})
    issues += validation._check_step_structure({"graph": graph})
    return issues