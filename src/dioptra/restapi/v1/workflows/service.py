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
"""The server-side functions that perform workflows endpoint operations."""
from typing import IO, Final

import structlog
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi import utils
from dioptra.restapi.db import db
from dioptra.restapi.errors import (
    DraftDoesNotExistError,
    DraftResourceModificationsCommitError,
    EntityDoesNotExistError,
)
from dioptra.restapi.v1.shared.resource_service import (
    ResourceIdService,
    ResourceService,
)

from .lib import views
from .lib.package_job_files import package_job_files
from .schema import FileTypes

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "workflow"


class JobFilesDownloadService(object):
    """The service methods for packaging job files for download."""

    def get(self, job_id: int, file_type: FileTypes, **kwargs) -> IO[bytes]:
        """Get the files needed to run a job and package them for download.

        Args:
            job_id: The identifier of the job.
            file_type: The type of file to package the job files into. Must be one of
                the values in the FileTypes enum.

        Returns:
            The packaged job files returned as a named temporary file.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job files download", job_id=job_id, file_type=file_type)

        experiment = views.get_experiment(job_id=job_id, logger=log)
        entry_point = views.get_entry_point(job_id=job_id, logger=log)
        entry_point_plugin_files = views.get_entry_point_plugin_files(
            job_id=job_id, logger=log
        )
        job_parameter_values = views.get_job_parameter_values(job_id=job_id, logger=log)
        plugin_parameter_types = views.get_plugin_parameter_types(
            job_id=job_id, logger=log
        )
        return package_job_files(
            job_id=job_id,
            experiment=experiment,
            entry_point=entry_point,
            entry_point_plugin_files=entry_point_plugin_files,
            job_parameter_values=job_parameter_values,
            plugin_parameter_types=plugin_parameter_types,
            file_type=file_type,
            logger=log,
        )


class DraftCommitService(object):
    """The service methods for commiting a Draft as a new ResourceSnapshot."""

    @inject
    def __init__(
        self,
        resource_service: ResourceService,
        resource_id_service: ResourceIdService,
    ) -> None:
        """Initialize the queue service.

        All arguments are provided via dependency injection.

        Args:
            resource_service: A ResourceService object.
            resource_id_service: A ResourceIdService object.
        """
        self._resource_service = resource_service
        self._resource_id_service = resource_id_service

    def commit_draft(self, draft_id: int, **kwargs) -> dict:
        """Commit the Draft as a new ResourceSnapshot

        Args:
            draft_id: The identifier of the draft.

        Returns:
            The packaged job files returned as a named temporary file.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("commit draft", draft_id=draft_id)

        draft = views.get_draft_resource(draft_id, logger=log)
        if draft is None:
            raise DraftDoesNotExistError(draft_resource_id=draft_id)

        if draft.payload["resource_id"] is None:
            resource = self._resource_service.create(
                resource_type=draft.resource_type,
                resource_data=draft.payload["resource_data"],
                group_id=draft.group_id,
                commit=False,
                log=log,
            )
        else:  # the draft contains modifications to an existing resource
            resource = views.get_latest_resource_snapshot(
                draft.resource_type, draft.resource_id
            )
            if resource is None:
                raise EntityDoesNotExistError(
                    draft.resource_type, resource_id=draft.resource_id
                )

            # if the underlying resource was modified since the draft was created,
            # raise an error with the information necessary to reconcile the draft.
            if draft.resource_snapshot_id != resource.latest_snapshot_id:
                prev_snapshot = views.get_resource_snapshot(
                    draft.resource_type, draft.resource_snapshot_id
                )
                if prev_snapshot is None:
                    raise EntityDoesNotExistError(
                        draft.resource_type, snapshot_id=draft.resource_snapshot_id
                    )

                curr_snapshot = views.get_resource_snapshot(
                    draft.resource_type, resource.latest_snapshot_id
                )
                if curr_snapshot is None:
                    raise EntityDoesNotExistError(
                        draft.resource_type, resource_id=draft.resource_id
                    )

                raise DraftResourceModificationsCommitError(
                    resource_type=draft.resource_type,
                    resource_id=draft.resource_id,
                    draft=utils.build_resource(
                        draft.resource_type, {draft.resource_type: draft}
                    ),
                    previous_snapshot=utils.build_resource(
                        draft.resource_type, prev_snapshot
                    ),
                    current_snapshot=utils.build_resource(
                        draft.resource_type, curr_snapshot
                    ),
                )

            resource = self._resource_service.modify(
                resource_id=draft.resource_id,
                resource_type=draft.resource_type,
                resource_data=draft.payload["resource_data"],
                group_id=draft.group_id,
                commit=False,
                log=log,
            )

        db.session.delete(draft)

        db.session.commit()

        return resource
