import datetime
from typing import List

import rq
from injector import inject

from mitre.securingai.restapi.app import db
from mitre.securingai.restapi.shared.job_queue.service import RQService

from .model import Job


class JobService(object):
    @inject
    def __init__(self, rq_service: RQService) -> None:
        self._rq_service = rq_service

    @staticmethod
    def get_all() -> List[Job]:
        return Job.query.all()

    @staticmethod
    def get_by_id(job_id: str) -> Job:
        return Job.query.get(job_id)

    def submit(self, new_job: Job) -> Job:
        timestamp = datetime.datetime.now()

        rq_job: rq.job.Job = self._rq_service.submit_mlflow_job(
            queue=new_job.queue,
            workflow_uri=new_job.workflow_uri,
            entry_point=new_job.entry_point,
            entry_point_kwargs=new_job.entry_point_kwargs,
        )

        new_job.job_id = rq_job.get_id()
        new_job.created_on = timestamp
        new_job.last_modified = timestamp

        db.session.add(new_job)
        db.session.commit()

        return new_job
