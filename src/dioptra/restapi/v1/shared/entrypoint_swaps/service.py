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
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 International
# license (CC BY 4.0). The disclaimers of the CC BY 4.0 license apply to all parts
# of the software developed or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode
import json

from itertools import product

import yaml
from src.dioptra.restapi.db import models
from src.dioptra.restapi.errors import EmptyGraphError
import structlog
from structlog.stdlib import BoundLogger
from typing import Any
from injector import inject

from dioptra.task_engine.issues import IssueSeverity, IssueType, ValidationIssue
from dioptra.restapi.v1.entrypoints.service import EntrypointIdService, EntrypointSnapshotIdService
from dioptra.restapi.v1.shared.task_engine_yaml.service import TaskEngineYamlService
from dioptra.restapi.v1.workflows.lib.views import get_plugin_plugin_files_from_plugin_snapshot_ids
from dioptra.sdk.utilities.entrypoint_swaps import render_swaps_graph
from dioptra.task_engine import util
from dioptra.task_engine.issues import IssueSeverity, IssueType, ValidationIssue

LOGGER: BoundLogger = structlog.stdlib.get_logger()

class SwapsValidationService(object):
    @inject
    def __init__(
        self,
        entrypoint_snapshot_id_service: EntrypointSnapshotIdService,
        task_engine_yaml_service: TaskEngineYamlService,
    ) -> None:
        self._entrypoint_snapshot_id_service = entrypoint_snapshot_id_service
        self._task_engine_yaml_service = task_engine_yaml_service

    def swaps_graph_validation(
        self,
        pre_rendered_task_graph: dict[str, Any],
    ) -> list["ValidationIssue"]:
        from dioptra.sdk.api.swappable_validation import get_json_schema
        from dioptra.task_engine.validation import _schema_validate

        return _schema_validate(pre_rendered_task_graph, get_json_schema)

    def validate_swap_output_matches(
        self, pre_rendered_task_graph: dict[str, Any], task_lookup_dict: dict[str, Any]
    ) -> tuple[list["ValidationIssue"], dict[str, Any]]:
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

                            output_parameters: list[models.PluginTaskOutputParameter] = (
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

    def build_task_lookup_dict(self, plugins: list[models.PluginPluginFile]):
        lookup = {}

        for pair in plugins:
            plugin = pair.plugin
            file = pair.plugin_file

            for task in file.tasks:
                if isinstance(task, models.FunctionTask):
                    # there must be a better way to check this

                    lookup[task.plugin_task_name] = {
                        "plugin_snapshot_id": plugin.resource_snapshot_id,
                        "pluginfile_filename": file.filename,
                        "task_name": task.plugin_task_name,
                        "output_parameters": task.output_parameters,
                    }

        return lookup

    def extract_swaps(self, task_graph: dict[str, Any]) -> dict[str, list[str]]:
        """Extract all swaps from a task graph.

        Args:
            task_graph: The task graph dictionary.

        Returns:
            A dictionary mapping swap names to lists of available aliases.
        """
        swaps = {}

        for step, task in task_graph.items():
            for swap_name, aliased_defns in task.items():
                if swap_name.startswith("?"):
                    swap_name_clean = swap_name[1:]  # Remove the '?' prefix
                    if swap_name_clean not in swaps:
                        swaps[swap_name_clean] = list(aliased_defns.keys())

        return swaps

    def validate_all_swap_combinations(
        self,
        group_id: int,
        task_graph_yaml: dict[str, Any],
        artifact_graph: str,
        plugin_plugin_files: list[models.PluginPluginFile],
        plugin_parameter_types: list[models.PluginTaskParameterType],
        entrypoint_parameters: list[dict[str, Any]],
        entrypoint_artifacts: list[dict[str, Any]],
        log: BoundLogger,
    ) -> list["ValidationIssue"]:
        """Validate all combinations of swaps in the task graph.

        Args:
            task_graph: The task graph dictionary.
            task_lookup_dict: Dictionary mapping task names to task metadata.
            task_engine_yaml_service: Service for building and validating task engine YAML.
            entrypoint_data: The entrypoint data adapter.
            plugin_parameter_types: Plugin parameter types.
            plugin_plugin_files: Plugin plugin files.

        Returns:
            A list of all validation issues found across all swap combinations.
        """
        import json
        from itertools import product

        from dioptra.sdk.utilities.entrypoint_swaps import render_swaps_graph
        from dioptra.restapi.v1.shared.entrypoint_validation import build_entrypoint_data_adapter

        swaps = self.extract_swaps(task_graph_yaml)

        if not swaps:
            return self._task_engine_yaml_service.validate(task_graph_yaml)

        swap_names = list(swaps.keys())
        alias_lists = [swaps[name] for name in swap_names]

        all_issues = []

        # all possible combinations of swap choices
        for combination in product(*alias_lists):
            swap_mapping = dict(zip(swap_names, combination))

            try:
                rendered_graph = render_swaps_graph(task_graph_yaml, swap_mapping)

                entrypoint_data = build_entrypoint_data_adapter(
                    json.dumps(rendered_graph),
                    artifact_graph,
                    entrypoint_parameters,
                    entrypoint_artifacts,
                    log
                )

                task_engine_dict = self._task_engine_yaml_service.build_dict(
                    entry_point=entrypoint_data,
                    plugin_plugin_files=plugin_plugin_files,
                    plugin_parameter_types=plugin_parameter_types,
                )

                issues = self._task_engine_yaml_service.validate(task_engine_dict)

                for issue in issues:
                    issue.message = f"[Swap combination {swap_mapping}] {issue.message}"
                    all_issues.append(issue)

            except Exception as e:
                all_issues.append(
                    ValidationIssue(
                        type_=IssueType.SEMANTIC,
                        severity=IssueSeverity.ERROR,
                        message=f"[Swap combination {swap_mapping}] Error rendering graph: {str(e)}",
                    )
                )

        return all_issues

class EntrypointSwapsValidationService(object):
    """Service that validates a swaps graph in the context of an entrypoint.

    It performs three checks:
    1. Uses :class:`DynamicGlobalParametersService` to determine which global
       parameters are required by the swaps graph.
    2. Ensures those globals are declared on the entrypoint (via
       :class:`EntrypointIdService`).
    3. Delegates to :class:`SwapsValidationService` for schema validation and
       output‑type matching.
    """

    @inject
    def __init__(
        self,
        swaps_validation_service: SwapsValidationService,
        entrypoint_id_service: EntrypointIdService,
        entrypoint_snapshot_id_service: EntrypointSnapshotIdService,
        task_engine_yaml_service: TaskEngineYamlService,
    ) -> None:
        self._swaps_validation_service = swaps_validation_service
        self._entrypoint_id_service = entrypoint_id_service
        self._entrypoint_snapshot_id_service = entrypoint_snapshot_id_service
        self._task_engine_yaml_service = task_engine_yaml_service

    def validate(
        self,
        group_id: int,
        swaps_graph: str,
        artifact_graph: str,
        entrypoint_parameters: list[dict[str, Any]],
        entrypoint_artifacts: list[dict[str, Any]],
        plugin_snapshot_ids: list[int],
        globals: dict[str, Any],
        **kwargs,
    ) -> dict[str, Any]:
        """Validate swaps graph against an entrypoint.

        Args:
            entrypoint_id: ID of the entrypoint to validate against.
            entrypoint_snapshot_id: Optional snapshot ID; ``None`` means latest.
            swaps_graph: YAML string of the swaps graph.
            plugin_snapshot_ids: Plugin snapshots required for output validation.
        Returns:
            Dictionary with keys:
                * schema_valid - boolean value describing whether the graph passes schema validation
                * rendered_validation_errors - a list of validation errors that occured across all combinations of swaps
                * missing_global_params - a list of global parameters required by the graph that were not declared as entrypoint parameters.
        """

        log: BoundLogger = kwargs.get("log", LOGGER.new())

        swaps_yaml = yaml.safe_load(swaps_graph)

        if swaps_yaml is None:
            raise EmptyGraphError("Provided swaps graph is empty.")

        # check for schema issues
        schema_issues = self._swaps_validation_service.swaps_graph_validation(
            pre_rendered_task_graph=swaps_yaml
        )

        # check for globals needed by graph that aren't parameters on the entrypoint
        required_globals: list[str] = globals.get("entrypoint_params", [])

        declared_globals = {p["name"] for p in entrypoint_parameters}
        declared_globals.update({a["name"] for a in entrypoint_artifacts})

        missing_globals = [g for g in required_globals if g not in declared_globals]
        missing_global_issues: list["ValidationIssue"] = []
        for missing in missing_globals:
            missing_global_issues.append(
                ValidationIssue(
                    type_=IssueType.SEMANTIC,
                    severity=IssueSeverity.ERROR,
                    message=f"Global parameter '{missing}' required by swaps but not declared on entrypoint.",
                )
            )


        # check that every combination of swaps possible is valid using existing validation

        plugin_plugin_files = get_plugin_plugin_files_from_plugin_snapshot_ids(
            plugin_snapshot_ids=plugin_snapshot_ids,
            logger=log
        )

        rendered_validation_issues = self._swaps_validation_service.validate_all_swap_combinations(
            group_id=group_id,
            artifact_graph=artifact_graph,
            task_graph_yaml=swaps_yaml,
            plugin_plugin_files=plugin_plugin_files,
            plugin_parameter_types=self._entrypoint_snapshot_id_service.get_group_plugin_parameter_types(
                group_id=group_id, logger=log
            ),
            entrypoint_parameters=entrypoint_parameters,
            entrypoint_artifacts=entrypoint_artifacts,
            log=log
        )

        schema_valid = len(schema_issues) == 0

        return {
            "schema_valid": schema_valid,
            "rendered_validation_errors": rendered_validation_issues,
            "missing_global_params": missing_globals,
        }
