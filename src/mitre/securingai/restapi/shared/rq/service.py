from typing import Optional, Union

import structlog
from redis import Redis
from redis.exceptions import RedisError
from rq.exceptions import NoSuchJobError
from rq.job import Job as RQJob
from rq.queue import Queue as RQQueue
from structlog.stdlib import BoundLogger

from mitre.securingai.restapi.job.model import Job

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class RQService(object):
    def __init__(self, redis: Redis, run_mlflow: str) -> None:
        self._redis = redis
        self._run_mlflow = run_mlflow

    def get_job_status(self, job: Job, **kwargs) -> str:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        rq_job: Optional[RQJob] = self.get_rq_job(job=job, log=log)

        if rq_job is None:
            return "finished"

        log.info("Fetching RQ job status", job_id=rq_job.get_id())

        return str(rq_job.get_status())

    def get_rq_job(self, job: Union[Job, str], **kwargs) -> Optional[RQJob]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        job_id: str = job.job_id if isinstance(job, Job) else job
        log.info("Fetching RQ job", job_id=job_id)

        try:
            rq_job: RQJob = RQJob.fetch(job_id, connection=self._redis)

        except (RedisError, NoSuchJobError):
            log.exception("RQ job not found", job_id=job_id)
            return None

        return rq_job

    def submit_mlflow_job(
        self,
        queue: str,
        workflow_uri: str,
        experiment_id: int,
        entry_point: str,
        entry_point_kwargs: Optional[str] = None,
        depends_on: Optional[str] = None,
        timeout: Optional[str] = None,
        **kwargs,
    ) -> RQJob:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        q: RQQueue = RQQueue(queue, default_timeout="24h", connection=self._redis)
        cmd_kwargs = {
            "workflow_uri": workflow_uri,
            "experiment_id": str(experiment_id),
            "entry_point": entry_point,
        }
        job_dependency: Optional[RQJob] = None

        if entry_point_kwargs is not None:
            cmd_kwargs["entry_point_kwargs"] = entry_point_kwargs

        if depends_on is not None:
            job_dependency = self.get_rq_job(depends_on, log=log)

        log.info(
            "Enqueuing job",
            function=self._run_mlflow,
            cmd_kwargs=cmd_kwargs,
            timeout=timeout,
            depends_on=job_dependency,
        )
        result: RQJob = q.enqueue(
            self._run_mlflow,
            kwargs=cmd_kwargs,
            timeout=timeout,
            depends_on=job_dependency,
        )

        return result
