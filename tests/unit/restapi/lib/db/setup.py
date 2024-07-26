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
from typing import Final

from sqlalchemy import insert
from sqlalchemy.orm import Session

from dioptra.restapi.db import models

ENTRY_POINT_PARAMETER_TYPES: Final[list[dict[str, str]]] = [
    {"parameter_type": "string"},
    {"parameter_type": "float"},
    {"parameter_type": "path"},
    {"parameter_type": "uri"},
]
JOB_STATUS_TYPES: Final[list[dict[str, str]]] = [
    {"status": "queued"},
    {"status": "started"},
    {"status": "deferred"},
    {"status": "finished"},
    {"status": "failed"},
]
USER_LOCK_TYPES: Final[list[dict[str, str]]] = [
    {"user_lock_type": "delete"},
]
GROUP_LOCK_TYPES: Final[list[dict[str, str]]] = [
    {"group_lock_type": "delete"},
]
RESOURCE_LOCK_TYPES: Final[list[dict[str, str]]] = [
    {"resource_lock_type": "delete"},
    {"resource_lock_type": "readonly"},
]
RESOURCE_TYPES: Final[list[dict[str, str]]] = [
    {"resource_type": "artifact"},
    {"resource_type": "entry_point"},
    {"resource_type": "experiment"},
    {"resource_type": "job"},
    {"resource_type": "ml_model"},
    {"resource_type": "plugin"},
    {"resource_type": "plugin_file"},
    {"resource_type": "plugin_task_parameter_type"},
    {"resource_type": "queue"},
    {"resource_type": "resource_snapshot"},
    {"resource_type": "ml_model_version"},
]
RESOURCE_DEPENDENCY_TYPES: Final[list[dict[str, str]]] = [
    {"parent_resource_type": "experiment", "child_resource_type": "entry_point"},
    {"parent_resource_type": "entry_point", "child_resource_type": "plugin"},
    {"parent_resource_type": "entry_point", "child_resource_type": "queue"},
    {"parent_resource_type": "plugin", "child_resource_type": "plugin_file"},
    {"parent_resource_type": "job", "child_resource_type": "artifact"},
    {"parent_resource_type": "job", "child_resource_type": "job"},
    {"parent_resource_type": "ml_model", "child_resource_type": "ml_model_version"},
]


def setup_ontology(session: Session) -> None:
    """Setup the ontology tables in the database.

    Args:
        session: The SQLAlchemy session object.
    """
    stmts = [
        insert(models.entry_point_parameter_types_table).values(
            ENTRY_POINT_PARAMETER_TYPES
        ),
        insert(models.job_status_types_table).values(JOB_STATUS_TYPES),
        insert(models.user_lock_types_table).values(USER_LOCK_TYPES),
        insert(models.group_lock_types_table).values(GROUP_LOCK_TYPES),
        insert(models.resource_lock_types_table).values(RESOURCE_LOCK_TYPES),
        insert(models.resource_types_table).values(RESOURCE_TYPES),
        insert(models.resource_dependency_types_table).values(
            RESOURCE_DEPENDENCY_TYPES
        ),
    ]

    for stmt in stmts:
        session.execute(stmt)

    session.commit()
