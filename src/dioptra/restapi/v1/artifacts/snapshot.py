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

import structlog
from sqlalchemy import select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import EntityDoesNotExistError
from dioptra.restapi.v1.entity_types import EntityTypes

RESOURCE_TYPE: Final[EntityTypes] = EntityTypes.ARTIFACT  # "artifact"
LOGGER: BoundLogger = structlog.stdlib.get_logger()

# This service has been split out to avoid a circular dependency with the jobs.service
# module if this class were included with the rest of the artifacts.service module
# classes. The repository patterns should hopefully resolve this and allow everything to
# be recombined once that refactor is complete.


class ArtifactSnapshotIdService(object):
    """The service methods for retrieving artifacts by their unique id."""

    def get(
        self, artifact_id: int, artifact_snapshot_id: int, **kwargs
    ) -> models.Artifact:
        """Run a query to get the Artifact for an entrypoint snapshot id.

        Args:
            artifact_id: The ID of the artifact resource the snapshot is associated with
            artifact_snapshot_id: The Snapshot ID of the artifact to retrieve

        Returns:
            The artifact.

        Raises:
            EntityDoesNotExistError: If the artifact is not found
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "get artifact snapshot",
            resource_id=artifact_id,
            resource_snapshot_id=artifact_snapshot_id,
        )
        artifact_resource_snapshot_stmt = select(models.Artifact).where(
            models.Artifact.resource_id == artifact_id,
            models.Artifact.resource_snapshot_id == artifact_snapshot_id,
        )
        artifact = db.session.scalar(artifact_resource_snapshot_stmt)

        if artifact is None:
            raise EntityDoesNotExistError(
                RESOURCE_TYPE,
                artifact_id=artifact_id,
                artifact_snapshot_id=artifact_snapshot_id,
            )
        return artifact
