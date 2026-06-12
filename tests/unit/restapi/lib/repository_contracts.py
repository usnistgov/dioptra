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
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import dioptra.restapi.db.models as models
from dioptra.restapi.v1.entity_types import EntityType
from tests.unit.restapi.lib import resource_factories

SnapshotFactory = Callable[[Any, Any, Any], models.ResourceSnapshot]
NextSnapshotFactory = Callable[[models.ResourceSnapshot], models.ResourceSnapshot]


@dataclass(frozen=True)
class ResourceRepositoryCase:
    id: str
    repo_fixture: str
    entity_type: EntityType
    snapshot_class: type[models.ResourceSnapshot]
    make_initial_snapshot: SnapshotFactory
    make_next_snapshot: NextSnapshotFactory
    make_wrong_resource_type_snapshot: SnapshotFactory


RESOURCE_REPOSITORY_CASES = [
    ResourceRepositoryCase(
        id="queue",
        repo_fixture="queue_repo",
        entity_type=EntityType.QUEUE,
        snapshot_class=models.Queue,
        make_initial_snapshot=resource_factories.make_queue,
        make_next_snapshot=resource_factories.make_queue_snapshot,
        make_wrong_resource_type_snapshot=(
            resource_factories.make_wrong_resource_type_queue
        ),
    ),
    ResourceRepositoryCase(
        id="type",
        repo_fixture="type_repo",
        entity_type=EntityType.PLUGIN_TASK_PARAMETER_TYPE,
        snapshot_class=models.PluginTaskParameterType,
        make_initial_snapshot=resource_factories.make_type,
        make_next_snapshot=resource_factories.make_type_snapshot,
        make_wrong_resource_type_snapshot=(
            resource_factories.make_wrong_resource_type_type
        ),
    ),
    ResourceRepositoryCase(
        id="experiment",
        repo_fixture="experiment_repo",
        entity_type=EntityType.EXPERIMENT,
        snapshot_class=models.Experiment,
        make_initial_snapshot=resource_factories.make_experiment,
        make_next_snapshot=resource_factories.make_experiment_snapshot,
        make_wrong_resource_type_snapshot=(
            resource_factories.make_wrong_resource_type_experiment
        ),
    ),
    ResourceRepositoryCase(
        id="entrypoint",
        repo_fixture="entrypoint_repo",
        entity_type=EntityType.ENTRY_POINT,
        snapshot_class=models.EntryPoint,
        make_initial_snapshot=resource_factories.make_entrypoint_for_contract,
        make_next_snapshot=resource_factories.make_entrypoint_snapshot,
        make_wrong_resource_type_snapshot=(
            resource_factories.make_wrong_resource_type_entrypoint
        ),
    ),
]
