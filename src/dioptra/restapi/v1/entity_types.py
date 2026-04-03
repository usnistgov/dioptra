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

from enum import Enum


class EntityType(Enum):
    """Entity enumeration used for the unified way of identifying
        entities as const-style name/enumerable tuples

    Args:
        Enum (_type_): [str, str] [DB-compatible name; User-friendly name]
    """

    NONE = "none", "Entity of Type NONE"
    UNDEFINED = "undefined", "Entity of Type 'Undefined'"

    JOB = "job", "Job"
    TAG = "tag", "Tag"
    USER = "user", "User"
    GROUP = "group", "Group"
    QUEUE = "queue", "Queue"
    METRIC = "metric", "Metric"
    RESOURCE = "resource", "Resource"
    EXPERIMENT = "experiment", "Experiment"
    # --- Model-Related Entities ---
    ML_MODEL = "ml_model", "ML Model"
    ML_FLOW_RUN = "ml_flow_run", "ML Flow Run"
    ML_MODEL_VERSION = "ml_model_version", "ML Model Version"
    # --- Artifact-Related Entities ---
    ARTIFACT = ("artifact", "Artifact")
    ARTIFACT_OUTPUT_PARAMETER = (
        "artifact_output_parameter",
        "Artifact Output Parameter",
    )
    ARTIFACT_TASK_OUTPUT_PARAMETER = (
        "artifact_task_output_parameter",
        "Artifact Task Output Parameter",
    )
    ARTIFACT_TASK_INPUT_PARAMETER = (
        "artifact_task_input_parameter",
        "Artifact Task Input Parameter",
    )
    # --- Entry-Point Entities ---
    ENTRY_POINT = "entry_point", "Entry Point"
    ENTRY_POINT_PLUGIN = "entry_point_plugin", "Entry Point Plugin"
    # --- Plugin-Related Entities ---
    PLUGIN = "plugin", "Plugin"
    PLUGIN_TASK = "plugin_task", "Plugin Task"
    PLUGIN_FILE = "plugin_file", "Plugin File"
    PLUGIN_TASK_PARAMETER = "plugin_task_parameter", "Plugin Task Parameter"
    PLUGIN_TASK_PARAMETER_TYPE = (
        "plugin_task_parameter_type",
        "Plugin Task Parameter Type",
    )

    db_schema_name: str  # DB-compatible name representation
    print_name: str  # User(UI)-friendly name representation

    def __new__(
        cls,
        original_name: str,
        readable_name: str,
    ):
        """Default constructor for stuffing EntityTypes Enum

        Args:
            original_name (str): DB-schema-safe entity type name
            readable_name (str): The name to be read by user in UI/UX/Logs/Errors

        Returns:
            _type_: The created const-style immutable tuple-member the enum
        """
        new_instance = object.__new__(cls)
        new_instance._value_ = original_name
        new_instance.db_schema_name = original_name
        new_instance.print_name = readable_name
        return new_instance

    @staticmethod
    def get_from_db_schema_name(db_name: str):
        try:
            return EntityType[db_name.upper()]
        except KeyError:
            return EntityType.UNDEFINED
