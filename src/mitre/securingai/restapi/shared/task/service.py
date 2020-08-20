
import os
import shlex
import subprocess
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
from typing import List, Optional

import rq
from flask import Flask

from mitre.securingai.restapi import create_app
from mitre.securingai.restapi.app import db
from mitre.securingai.restapi.job.model import Job
from mitre.securingai.restapi.shared.job_queue.model import JobStatus


def _update_task_status(status: JobStatus) -> None:
    app: Flask = create_app(env=os.getenv("AI_RESTAPI_ENV"))
    rq_job: Optional[rq.job.Job] = rq.get_current_job()

    if rq_job is None:
        return None

    with app.app_context():
        job = Job.query.get(rq_job.get_id())

        if job.status != status:
            job.update(changes={"status": status})
            db.session.commit()


def run_mlflow_task(
    workflow_uri: str,
    entry_point: str,
    conda_env: str = "base",
    entry_point_kwargs: Optional[str] = None,
) -> CompletedProcess:
    cmd: List[str] = [
        "/usr/local/bin/run-mlflow-job.sh",
        "--s3-workflow",
        workflow_uri,
        "--entry-point",
        entry_point,
        "--conda-env",
        conda_env,
    ]

    if entry_point_kwargs is not None:
        cmd.extend(shlex.split(entry_point_kwargs))

    with TemporaryDirectory(dir=os.getenv("AI_WORKDIR")) as tmpdir:
        _update_task_status(status=JobStatus.started)
        p = subprocess.run(args=cmd, cwd=tmpdir)

    if p.returncode > 0:
        _update_task_status(status=JobStatus.failed)
        return p

    _update_task_status(status=JobStatus.finished)
    return p
