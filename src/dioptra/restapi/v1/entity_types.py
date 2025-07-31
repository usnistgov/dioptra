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
from enum import Enum

"""_summary_

Returns:
    _type_: _description_

Example:

import sys
import os
# Define the path to the directory containing your module
module_directory = "/Users/dac4/di2run/dio-src/src/dioptra/restapi/v1/" 
# Add the directory to sys.path
sys.path.append(module_directory)
import entity_types as et
et.EntityTypes.get_from_string('job')
et.EntityTypes.get_from_string('plugin_task_parameter')
[print(f"{x.name=}\t{x.value=}\t{x.schema_name=}\t{x.print_name=}") for x in et.EntityTypes]

from entity_types import EntityType

from dioptra.restapi.v1.entity_types import EntityTypes

dioptra.restapi.v1.entity_types

Final[EntityTypes]

EntityTypes.get_from_string

EntityTypes.QUEUE
EntityTypes.USER
EntityTypes.RESOURCE

.get_db_schema_name()
"""


class EntityTypes(Enum):
    """Entity enumeration used for the unified way of identifying entities as const-style name/enumerable tuples

    Args:
        Enum (_type_): _description_
    """

    @staticmethod
    def get_from_string(resource_type_name: str | None):
        """
         EntityTypes.get_from_string ('entity_type')
        Args:
            value (_type_): _description_

        Returns:
            _type_: _description_
        """
        if not resource_type_name:
            # print(f"1. {resource_type_name=} ")
            return EntityTypes.NONE
        else:
            name = EntityTypes.to_snake_case(resource_type_name).upper()
            # print(f"pre-2. {name=} ")
            for current_value in EntityTypes.list_names():
                # for entry in
                # print(f"2. {current_value=} vs. {name=} ")
                if name == current_value:
                    return EntityTypes[name]
        print(f"!!! {resource_type_name=} Was Not Found in ENUM !!!")
        return EntityTypes.UNDEFINED
        # ----------------------------------------------------------------------

    @classmethod
    def list_names(cls) -> list[str]:
        return list(map(lambda c: c.name, cls))
        # ----------------------------------------------------------------------

    def __str__(self):
        return self.db_schema_name
        # ----------------------------------------------------------------------

    def __repr__(self):
        return self.db_schema_name
        # ----------------------------------------------------------------------

    db_schema_name: str
    ui_print_name: str

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
        new_instance.ui_print_name = readable_name
        return new_instance
        # ----------------------------------------------------------------------

    NONE = "none", "Entity of Type NONE"
    UNDEFINED = "undefined", "Entity of Type 'Undefined'"
    # --- STRANGE CORNER-CASES ---
    PASSWORD = "password", "Password"
    # found by "RESOURCE_TYPE:"" search in files
    JOB = "job", "Job"
    TAG = "tag", "Tag"
    USER = "user", "User"
    GROUP = "group", "Group"
    QUEUE = "queue", "Queue"
    METRIC = "metric", "Metric"
    RESOURCE = "resource", "Resource"
    WORKFLOW = "workflow", "Workflow"
    EXPERIMENT = "experiment", "Experiment"

    ML_FLOW_RUN = "ml_flow_run", "M.L. Flow Run"
    ML_MODEL = "ml_model", "M.L. Model"
    ML_MODEL_VERSION = "ml_model_version", "M.L. Model Version"
    # --- Artifact-Related Entities ---
    HAS_DRAFT = "has_draft", "Has Draft"
    ARTIFACT = "artifact", "Artifact"
    ARTIFACT_OUTPUT_PARAMETER = (
        "artifact_output_parameter",
        "'Artifact Output Parameter'",
    )
    ARTIFACT_TASK_OUTPUT_PARAMETER = (
        "artifact_task_output_parameter",
        "'Artifact Task Output Parameter'",
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
    # --------------------------------------------------------------------------

    @staticmethod
    def to_snake_case(text_to_snake: str) -> str:
        """Converts a string to lower-case snake_case format.
        Handles various input formats like camelCase, PascalCase,
        and strings with spaces, comas, hyphens, colons,
        semicolons, or hyphens.

        Args:
            text_to_snake (str): The text to format

        Returns:
            str: _description_
        """
        # Replace punctuation with spaces
        text_to_snake = (
            text_to_snake.replace("-", " ")
            .replace(",", " ")
            .replace(".", " ")
            .replace(";", " ")
            .replace(":", " ")
        )
        # Replace spaces with underscores and convert to lowercase
        # Insert underscore before uppercase letters in camelCase/PascalCase
        # Handles cases like:
        #   "PascalCase" -> "Pascal_Case" and
        #   "varInCamelCase" -> "var_In_Camel_Case"
        text_to_snake = re.sub(r"(?<!^)(?=[A-Z])", " ", text_to_snake)
        # Clean multiple spaces by collapsing them, if they happen
        text_to_snake = re.sub(r"\s+", " ", text_to_snake).strip()
        # Replace spaces with underscores
        return text_to_snake.replace(" ", "_").lower()
        # ------------------------------------------------------------------

    def get_db_schema_name(self) -> str:
        """Returns current instance name/key

        Returns:
            str: returns inst-ENUM.all-lower-case - snake
        """
        if self.db_schema_name == EntityTypes.to_snake_case(self.db_schema_name):
            return self.db_schema_name
        else:
            return EntityTypes.to_snake_case(self.db_schema_name)
        # ---------------------------------------------------------------------

    def get_original_name(self) -> str:
        """Returns current Entity's key/db-schema-safe Name

        Returns:
            str: returns inst-ENUM.schema_name
        """
        return self.db_schema_name
        # ----------------------------------------------------------------------

    def get_print_name(self) -> str:
        """Returns current instance Human-Readable Name

        Returns:
            str: returns inst-ENUM.print_name

        """
        return self.ui_print_name
        # ----------------------------------------------------------------------

    def get_an_article(self) -> str:
        """Returns proper form on an indefinite article

        Returns:
            str: The article applicable to the EntityType instance
        """
        return "an" if self.ui_print_name.strip()[0].lower() in "aeiou" else "a"
        # ----------------------------------------------------------------------
