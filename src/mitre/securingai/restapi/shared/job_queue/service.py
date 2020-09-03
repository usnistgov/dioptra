
from typing import Optional, Union

import rq
from redis import Redis
from redis.exceptions import RedisError
from rq.exceptions import NoSuchJobError

from mitre.securingai.restapi.job.model import Job

from .model import JobStatus, JobQueue


class RQService(object):
    def __init__(self, redis: Redis, run_mlflow: str) -> None:
        self._redis = redis
        self._run_mlflow = run_mlflow

    def get_job_status(self, job: Job) -> JobStatus:
        job: Optional[rq.job.Job] = self.get_rq_job(job=job)

        if job is None:
            return JobStatus.finished

        return JobStatus[job.get_status()]

    def get_rq_job(self, job: Union[Job, str]) -> Optional[rq.job.Job]:
        job_id: str = job.job_id if isinstance(job, Job) else job

        try:
            rq_job: rq.job.Job = rq.job.Job.fetch(job_id, connection=self._redis)

        except (RedisError, NoSuchJobError):
            return None

        return rq_job

    def submit_mlflow_job(
        self,
        queue: JobQueue,
        workflow_uri: str,
        entry_point: str,
        entry_point_kwargs: Optional[str] = None,
        depends_on: Optional[str] = None,
        timeout: Optional[str] = None,
    ) -> rq.job.Job:
        cmd_kwargs = {
            "workflow_uri": workflow_uri,
            "entry_point": entry_point,
        }
        job_dependency: Optional[rq.job.Job] = None

        if entry_point_kwargs is not None:
            cmd_kwargs["entry_point_kwargs"] = entry_point_kwargs

        if depends_on is not None:
            job_dependency = self.get_rq_job(depends_on)

        q: rq.Queue = rq.Queue(queue.name, default_timeout="24h", connection=self._redis)
        result: rq.job.Job = q.enqueue(
            self._run_mlflow, kwargs=cmd_kwargs, timeout=timeout, depends_on=job_dependency
        )

        return result
