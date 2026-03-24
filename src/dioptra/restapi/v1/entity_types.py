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

from dioptra.restapi.errors import DioptraError


class EntityType(Enum):
    ARTIFACT = "artifact", "Artifact"
    ENTRY_POINT = "entry_point", "Entry Point"
    EXPERIMENT = "experiment", "Experiment"
    GROUP = "group", "Group"
    JOB = "job", "Job"
    ML_MODEL = "ml_model", "ML Model"
    ML_MODEL_VERSION = "ml_model_version", "ML Model Version"
    NONE = "none", "Entity of Type NONE"
    PLUGIN = "plugin", "Plugin"
    PLUGIN_FILE = "plugin_file", "Plugin File"
    PLUGIN_TASK_PARAMETER_TYPE = (
        "plugin_task_parameter_type",
        "Plugin Task Parameter Type",
    )
    QUEUE = "queue", "Queue"
    RESOURCE = "resource", "Resource"
    TAG = "tag", "Tag"
    USER = "user", "User"

    db_table_name: str
    display_name: str

    def __new__(cls, db_table_name: str, display_name: str) -> "EntityType":
        """Default constructor for stuffing EntityTypes Enum

        Args:
            db_table_name (str): The name of the database table for the Entity
            display_name (str): The name to be displayed in UI/UX/Logs/Errors

        Returns:
            _type_: The created const-style immutable tuple-member the enum
        """
        new_instance = object.__new__(cls)
        new_instance._value_ = db_table_name
        new_instance.db_table_name = db_table_name
        new_instance.display_name = display_name
        return new_instance

    @staticmethod
    def get_from_db_table_name(db_table_name: str) -> "EntityType":
        try:
            return EntityType[db_table_name.upper()]
        except KeyError as e:
            raise DioptraError("Invalid EntityType: {db_table_name}") from e
