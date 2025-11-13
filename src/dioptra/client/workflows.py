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
from typing import Any, ClassVar, Final, Literal, TypeVar

from .base import (
    CollectionClient,
    DioptraFile,
    IllegalArgumentError,
)

T = TypeVar("T")

DYNAMIC_GLOBAL_PARAMETERS: Final[str] = "dynamicGlobalParameters"
VALIDATE_ENTRYPOINT: Final[str] = "validateEntrypoint"
SIGNATURE_ANALYSIS: Final[str] = "pluginTaskSignatureAnalysis"
RESOURCE_IMPORT: Final[str] = "resourceImport"
DRAFT_COMMIT: Final[str] = "draftCommit"


class WorkflowsCollectionClient(CollectionClient[T]):
    """The client for managing Dioptra's /workflows collection.

    Attributes:
        name: The name of the collection.
    """

    name: ClassVar[str] = "workflows"

    def analyze_plugin_task_signatures(self, python_code: str) -> T:
        """
        Requests signature analysis for the functions in an annotated python file.

        Args:
            python_code: The contents of the python file.
            filename: The name of the file.

        Returns:
            The response from the Dioptra API.

        """

        return self._session.post(
            self.url,
            SIGNATURE_ANALYSIS,
            json_={"pythonCode": python_code},
        )

    def import_resources(
        self,
        group_id: int,
        source: str | DioptraFile | list[DioptraFile],
        config_path: str | None = None,
        resolve_name_conflicts_strategy: Literal["fail", "overwrite"] | None = None,
    ):
        """
        Import resources from a archive file or git repository

        Args:
            group_id: The group to import resources into
            source: The source to import from. Can be a str containing a git url, a
                DioptraFile containing an archive file or a list[DioptraFile]
                containing resource files.
            config_path: The path to the toml configuration file in the import source.
                If None, the API will use "dioptra.toml" as the default. Defaults to
                None.
            resolve_name_conflicts_strategy: The strategy for resolving name conflicts.
                Either "fail" or "overwrite". If None, the API will use "fail" as the
                default. Defaults to None.

        Raises:
            IllegalArgumentError: If more than one import source is provided or if no
                import source is provided.
        """
        data: dict[str, Any] = {"group": str(group_id)}
        files_: dict[str, DioptraFile | list[DioptraFile]] = {}

        if not isinstance(source, (str, DioptraFile, list)):
            raise IllegalArgumentError(
                "Illegal type for source (reason: must be one of str, DioptraFile, "
                f"or list[DioptraFile]): {type(source)}"
            )

        if isinstance(source, list):
            if not all(isinstance(x, DioptraFile) for x in source):
                illegal_types = {
                    type(x).__name__ for x in source if not isinstance(x, DioptraFile)
                }
                raise IllegalArgumentError(
                    "Illegal type for source (reason: list contains type(s) other "
                    f"than DioptraFile): {', '.join(sorted(illegal_types))}"
                )

            data["sourceType"] = "upload_files"
            files_["files"] = source

        if isinstance(source, str):
            data["sourceType"] = "git"
            data["gitUrl"] = source

        if isinstance(source, DioptraFile):
            data["sourceType"] = "upload_archive"
            files_["archiveFile"] = source

        if config_path is not None:
            data["configPath"] = config_path

        if resolve_name_conflicts_strategy is not None:
            data["resolveNameConflictsStrategy"] = resolve_name_conflicts_strategy

        return self._session.post(
            self.url, RESOURCE_IMPORT, data=data, files=files_ or None
        )

    def commit_draft(
        self,
        draft_id: str | int,
    ) -> T:
        """
        Commit a draft as a new resource snapshot.

        The draft can be a draft of a new resource or a draft modifications to an
        existing resource.

        Args:
            draft_id: The draft id, an intiger.

        Returns:
            A dictionary containing the contents of the new resource.
        """

        return self._session.post(self.url, DRAFT_COMMIT, str(draft_id))

    def validate_entrypoint(
        self,
        group_id: int,
        task_graph: str,
        plugin_snapshots: list[int],
        entrypoint_parameters: list[dict[str, Any]],
    ) -> T:
        """Validate a set of proposed inputs for an entrypoint resource.

        Args:
            group_id: The ID of the group validating the entrypoint resource.
            task_graph: The proposed task graph for the entrypoint resource.
            plugin_snapshots: A list of identifiers for the plugin snapshots that will
                be attached to the Entrypoint resource.
            entrypoint_parameters: The proposed list of parameters for the entrypoint
                resource.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {
            "group": group_id,
            "taskGraph": task_graph,
            "pluginSnapshots": plugin_snapshots,
            "parameters": entrypoint_parameters,
        }

        return self._session.post(self.url, VALIDATE_ENTRYPOINT, json_=json_)

    def task_graph_global_params(
        self,
        entrypoint_id: int,
        entrypoint_snapshot_id: int,
        swaps: dict[str, str]
    ) -> T:
        
        json_ = {
            "entrypointId": entrypoint_id,
            "entrypointSnapshotId": entrypoint_snapshot_id,
            "swapChoices": swaps,
        }
        
        return self._session.post(self.url, DYNAMIC_GLOBAL_PARAMETERS, json_=json_)
