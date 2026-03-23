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

from dioptra.restapi.db.models.plugins import (
    FunctionTask,
    PluginPluginFile,
    PluginTaskOutputParameter,
)
from dioptra.sdk.api.swappable_validation import get_json_schema
from dioptra.task_engine.issues import IssueSeverity, IssueType, ValidationIssue
from dioptra.task_engine.validation import _schema_validate


class SwapsValidationService(object):
    def swaps_graph_validation(
        self,
        pre_rendered_task_graph: dict[str, Any],
    ) -> list[ValidationIssue]:
        return _schema_validate(pre_rendered_task_graph, get_json_schema)

    def validate_swap_output_matches(
        self, pre_rendered_task_graph: dict[str, Any], task_lookup_dict: dict[str, Any]
    ) -> tuple[list[ValidationIssue], dict[str, Any]]:
        mismatched_aliases = {}
        swap_tasks: dict[str, Any] = {}
        collected_no_tasks_found = []

        for _step, task in pre_rendered_task_graph.items():
            for swap_name, aliased_defns in task.items():
                if swap_name.startswith("?"):
                    output_types = set()
                    swap_dict = {}

                    for alias, definition in aliased_defns.items():
                        # figure out whether its long or short form
                        if "task" in definition:
                            # long version
                            task_name = definition["task"]
                        else:
                            # short version - should be exactly one key in here
                            task_name = list(definition.keys())[0]

                        # get the output type of task_name in the plugin
                        if task_name in task_lookup_dict:
                            swap_dict[alias] = {
                                "plugin_snapshot_id": task_lookup_dict[task_name][
                                    "plugin_snapshot_id"
                                ],
                                "pluginfile_filename": task_lookup_dict[task_name][
                                    "pluginfile_filename"
                                ],
                                "task_name": task_lookup_dict[task_name]["task_name"],
                            }

                            output_parameters: list[PluginTaskOutputParameter] = (
                                task_lookup_dict[task_name]["output_parameters"]
                            )
                            output_types.add(
                                tuple(
                                    [
                                        parameter.parameter_type.name
                                        for parameter in output_parameters
                                    ]
                                )
                            )
                        else:
                            collected_no_tasks_found.append(
                                ValidationIssue(
                                    type_=IssueType.SEMANTIC,
                                    severity=IssueSeverity.ERROR,
                                    message=f"In swap '{swap_name}', task with name '{task_name}' not found in registered tasks.",
                                )
                            )

                    swap_tasks[swap_name] = swap_dict

                    if len(output_types) > 1:
                        mismatched_aliases[swap_name] = output_types

        return collected_no_tasks_found + [
            ValidationIssue(
                type_=IssueType.TYPE,
                severity=IssueSeverity.ERROR,
                message=f"Swap '{swap_name}' contains mismatched output types: {types}",
            )
            for swap_name, types in mismatched_aliases.items()
        ], swap_tasks

    def build_task_lookup_dict(self, plugins: list[PluginPluginFile]):
        lookup = {}

        for pair in plugins:
            plugin = pair.plugin
            file = pair.plugin_file

            for task in file.tasks:
                if isinstance(task, FunctionTask):
                    # there must be a better way to check this

                    lookup[task.plugin_task_name] = {
                        "plugin_snapshot_id": plugin.resource_snapshot_id,
                        "pluginfile_filename": file.filename,
                        "task_name": task.plugin_task_name,
                        "output_parameters": task.output_parameters,
                    }

        return lookup
