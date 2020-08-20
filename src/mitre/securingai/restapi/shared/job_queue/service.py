
from typing import Optional

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

    def get_rq_job(self, job: Job) -> Optional[rq.job.Job]:
        try:
            rq_job: rq.job.Job = rq.job.Job.fetch(job.job_id, connection=self._redis)

        except (RedisError, NoSuchJobError):
            return None

        return rq_job

    def submit_mlflow_job(
        self,
        queue: JobQueue,
        workflow_uri: str,
        entry_point: str,
        entry_point_kwargs=None,
    ) -> rq.job.Job:
        cmd_kwargs = {
            "workflow_uri": workflow_uri,
            "entry_point": entry_point,
        }

        if entry_point_kwargs is not None:
            cmd_kwargs["entry_point_kwargs"] = entry_point_kwargs

        q: rq.Queue = rq.Queue(queue.name, connection=self._redis)
        result: rq.job.Job = q.enqueue(self._run_mlflow, kwargs=cmd_kwargs)

        return result
