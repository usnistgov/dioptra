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
"""The server-side functions that perform job endpoint operations."""
from __future__ import annotations

import datetime
import uuid
from pathlib import Path
from typing import List, Optional

import structlog
from injector import inject
from rq.job import Job as RQJob
from structlog.stdlib import BoundLogger
from werkzeug.utils import secure_filename

from dioptra.restapi.app import db
from dioptra.restapi.experiment.errors import ExperimentDoesNotExistError
from dioptra.restapi.experiment.service import ExperimentService
from dioptra.restapi.queue.errors import QueueDoesNotExistError
from dioptra.restapi.queue.service import QueueService
from dioptra.restapi.shared.rq.service import RQService
from dioptra.restapi.shared.s3.service import S3Service

from .errors import JobWorkflowUploadError
from .model import Group, GroupForm, GroupFormData
from .schema import GroupFormSchema

from sqlalchemy.exc import IntegrityError

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class GroupService(object):
    @inject
    def __init__(
        self,
        group_form_schema: GroupFormSchema,
    ) -> None:
        self._group_form_schema = group_form_schema

    @staticmethod
    def create(name: str, **kwargs) -> Group:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841
        timestamp = datetime.datetime.now()

        return Group(
            id = uuid.uuid4(),
            name=name,
            creator_id= current_user.id, 
            owner_id= current_user.id,
            created_on=timestamp,
            deleted= False
        )

    @staticmethod
    def get_all(**kwargs) -> List[Group]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return Group.query.all()  # type: ignore

    @staticmethod
    def get_by_id(group_id: id, **kwargs) -> Group:
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841

        return Group.query.get(group_id)  # type: ignore

    def extract_data_from_form(self, group_form: GroupForm, **kwargs) -> GroupFormData:
        from dioptra.restapi.models import Experiment, Queue

        log: BoundLogger = kwargs.get("log", LOGGER.new())

        group_form_data: GroupFormData = self._group_form_schema.dump(group_form)

        return group_form_data

    def submit(self, group_form_data: GroupFormData, **kwargs) -> Group:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        new_group: Group = self.create(group_form_data, log=log)

        db.session.add(new_group)
        db.session.commit()

        log.info("Group submission successful", group_id=new_group.id)

        return new_group
    
    def delete(self, id: int, **kwargs) -> bool:

        group = self.get_by_id(id)
        group.deleted = True
        try:
            db.session.commit()

            return True
        except IntegrityError as e:
            db.session.rollback()
            return False
