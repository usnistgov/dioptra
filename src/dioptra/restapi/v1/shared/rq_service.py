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
from redis import Redis
from rq.queue import Queue as RQQueue
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()

TIMEOUT_24_HOURS: Final[int] = 24 * 3600
RUN_V1_DIOPTRA_JOB_FUNC: Final[str] = "dioptra.rq.tasks.run_v1_dioptra_job"


class RQServiceV1(object):
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def submit(
        self,
        job_id: int,
        experiment_id: int,
        queue: str,
        timeout: str | None = None,
    ):
        log: BoundLogger = LOGGER.new()

        cmd_kwargs = {
            "job_id": job_id,
            "experiment_id": experiment_id,
        }

        log.info(
            "Enqueuing job",
            function=RUN_V1_DIOPTRA_JOB_FUNC,
            job_id=job_id,
            cmd_kwargs=cmd_kwargs,
            timeout=timeout,
        )

        q = RQQueue(queue, default_timeout=TIMEOUT_24_HOURS, connection=self._redis)
        q.enqueue(
            RUN_V1_DIOPTRA_JOB_FUNC,
            kwargs=cmd_kwargs,
            job_id=str(job_id),
            timeout=timeout,
        )
