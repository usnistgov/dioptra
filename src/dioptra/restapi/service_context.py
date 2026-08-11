# This Software (Dioptra) is being made available as a public service by the
# National Institute of Standards and Technology (NIST), an Agency of the United
# States Department of Commerce. This software was developed in part by employees of
# NIST and in part by NIST contractors. Copyright in portions of this software that
# were developed by NIST contractors has been licensed or assigned to NIST. Pursuant
# to Title 17 United Code Section 105, works of NIST employees are not subject to
# copyright protection in the United States. However, NIST may hold international
# copyright in software created by its employees and domestic copyright (or licensing
# rights) in portions of software that were assigned or licensed to NIST. To the
# extent that NIST holds copyright in this software, it is being made available under
# the Creative Commons Attribution 4.0 International license (CC BY 4.0). The
# disclaimers of the CC BY 4.0 license apply to all parts of the software developed
# or licensed by NIST.
#
# ACCESS THE FULL CC BY 4.0 LICENSE HERE:
# https://creativecommons.org/licenses/by/4.0/legalcode
from dataclasses import dataclass

from injector import inject

from dioptra.restapi.db.unit_of_work import UnitOfWork
from dioptra.restapi.v1.shared.job_queue import JobQueueProtocol
from dioptra.restapi.v1.shared.job_run_store import JobRunStoreProtocol


@dataclass
class ServiceContext:
    uow: UnitOfWork
    job_queue: JobQueueProtocol
    job_run_store: JobRunStoreProtocol


class ServiceContextService:
    @inject
    def __init__(self, context: ServiceContext) -> None:
        """Initialize the service context service.

        All arguments are provided via dependency injection.

        Args:
            context: A ServiceContext instance.
        """
        self._context = context
        self._uow = context.uow
