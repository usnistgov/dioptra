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

from typing import Any, Dict, Optional, Union

import structlog
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class MockRQJob(object):
    def __init__(
        self,
        id: str = "4520511d-678b-4966-953e-af2d0edcea32",
        queue: Optional[str] = None,
        job_timeout: Optional[int] = None,
        cmd_kwargs: Optional[Dict[str, Any]] = None,
        depends_on: Optional[Union[str, "MockRQJob"]] = None,
    ) -> None:
        """Store the prepared job data used by the test queue.

        Args:
            id: Job identifier on the queue.
            queue: Name of the target queue.
            job_timeout: Execution time limit in seconds.
            cmd_kwargs: Keyword arguments for the worker function.
            depends_on: Optional job that must run first.
        """
        LOGGER.info(
            "Mocking rq.job.Job instance",
            id=id,
            queue=queue,
            job_timeout=job_timeout,
            cmd_kwargs=cmd_kwargs,
            depends_on=depends_on,
        )
        self.queue = queue
        self.job_timeout = job_timeout
        self.cmd_kwargs = cmd_kwargs
        self._id = id
        self._dependency_ids = None

        if depends_on is not None:
            self._dependency_ids = [
                depends_on.id if isinstance(depends_on, MockRQJob) else depends_on
            ]

    @classmethod
    def fetch(cls, id: str, *args, **kwargs) -> "MockRQJob":
        LOGGER.info(
            "Mocking rq.job.Job.fetch() function", id=id, args=args, kwargs=kwargs
        )
        return cls(id=id)

    def get_id(self) -> str:
        LOGGER.info("Mocking rq.job.Job.get_id() function")
        return self._id

    def get_status(self) -> str:
        LOGGER.info("Mocking rq.job.Job.get_status() function")
        return "started"

    @property
    def id(self) -> str:
        LOGGER.info("Mocking rq.job.Job.id getter")
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        LOGGER.info("Mocking rq.job.Job.id setter", value=value)
        self._id = value

    @property
    def dependency(self) -> Optional["MockRQJob"]:
        LOGGER.info("Mocking rq.job.Job.dependency getter")
        if not self._dependency_ids:
            return None

        return self.fetch(self._dependency_ids[0])


class MockRQQueue(object):
    def __init__(self, *args, **kwargs):
        LOGGER.info("Mocking rq.Queue instance", args=args, kwargs=kwargs)
        self.name = kwargs.get("name") or args[0]
        self.default_timeout = kwargs.get("default_timeout")

    def create_job(
        self, func: str, *, kwargs: dict[str, Any], job_id: str, timeout: int | None
    ) -> MockRQJob:
        """Prepare a job without connecting to Redis.

        Args:
            func: Qualified name of the function the worker will execute.
            kwargs: Keyword arguments for the worker function.
            job_id: ID used to identify the job on the queue.
            timeout: Execution time limit in seconds, or None for the queue default.

        Returns:
            A test job with the requested payload and execution time limit.
        """
        LOGGER.info("Mocking rq.Queue.create_job() function", func=func)
        return MockRQJob(
            id=job_id,
            queue=self.name,
            job_timeout=self.default_timeout if timeout is None else timeout,
            cmd_kwargs=kwargs,
        )

    def enqueue_job(self, job: MockRQJob) -> MockRQJob:
        """Acknowledge a test job without connecting to Redis.

        Args:
            job: Prepared job to simulate delivering.

        Returns:
            The acknowledged job.
        """
        LOGGER.info("Mocking rq.Queue.enqueue_job() function", job_id=job.id)
        return job
