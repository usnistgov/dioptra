import datetime

from .interface import JobUpdateInterface
from mitre.securingai.restapi.app import db
from mitre.securingai.restapi.shared.job_queue.model import JobQueue, JobStatus


class Job(db.Model):  # type: ignore
    __tablename__ = "jobs"

    job_id = db.Column(db.String(36), primary_key=True)
    created_on = db.Column(db.DateTime())
    last_modified = db.Column(db.DateTime())
    queue = db.Column(db.Enum(JobQueue), index=True)
    timeout = db.Column(db.Text())
    workflow_uri = db.Column(db.Text())
    entry_point = db.Column(db.Text())
    entry_point_kwargs = db.Column(db.Text())
    depends_on = db.Column(db.String(36))
    status = db.Column(db.Enum(JobStatus), default=JobStatus.queued)

    def update(self, changes: JobUpdateInterface):
        self.last_modified = datetime.datetime.now()

        for key, val in changes.items():
            setattr(self, key, val)

        return self
