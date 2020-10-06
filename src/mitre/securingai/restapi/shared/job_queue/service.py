
from typing import Optional, Union

import rq
import structlog
from redis import Redis
from redis.exceptions import RedisError
from rq.exceptions import NoSuchJobError
from structlog import BoundLogger
from structlog._config import BoundLoggerLazyProxy

from mitre.securingai.restapi.job.model import Job

from .model import JobStatus, JobQueue


LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


class RQService(object):
    def __init__(self, redis: Redis, run_mlflow: str) -> None:
        self._redis = redis
        self._run_mlflow = run_mlflow

    def get_job_status(self, job: Job, **kwargs) -> JobStatus:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        job: Optional[rq.job.Job] = self.get_rq_job(job=job, log=log)
        log.info("Fetching RQ job status", job_id=job.get_id())

        if job is None:
            return JobStatus.finished

        return JobStatus[job.get_status()]

    def get_rq_job(self, job: Union[Job, str], **kwargs) -> Optional[rq.job.Job]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        job_id: str = job.job_id if isinstance(job, Job) else job
        log.info("Fetching RQ job", job_id=job_id)

        try:
            rq_job: rq.job.Job = rq.job.Job.fetch(job_id, connection=self._redis)

        except (RedisError, NoSuchJobError):
            log.exception("RQ job not found", job_id=job_id)
            return None

        return rq_job

    def submit_mlflow_job(
        self,
        queue: JobQueue,
        workflow_uri: str,
        experiment_id: int,
        entry_point: str,
        entry_point_kwargs: Optional[str] = None,
        depends_on: Optional[str] = None,
        timeout: Optional[str] = None,
        **kwargs,
    ) -> rq.job.Job:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        q: rq.Queue = rq.Queue(
            queue.name, default_timeout="24h", connection=self._redis
        )
        cmd_kwargs = {
            "workflow_uri": workflow_uri,
            "experiment_id": str(experiment_id),
            "entry_point": entry_point,
        }
        job_dependency: Optional[rq.job.Job] = None

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
        result: rq.job.Job = q.enqueue(
            self._run_mlflow,
            kwargs=cmd_kwargs,
            timeout=timeout,
            depends_on=job_dependency,
        )

        return result
