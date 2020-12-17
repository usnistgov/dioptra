
import os
import shlex
import subprocess
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
from typing import List, Optional

import structlog
from rq.job import Job as RQJob
from rq.job import get_current_job
from structlog import BoundLogger
from structlog._config import BoundLoggerLazyProxy

LOGGER: BoundLoggerLazyProxy = structlog.get_logger()


def run_mlflow_task(
    workflow_uri: str,
    entry_point: str,
    experiment_id: str,
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
        "--experiment-id",
        experiment_id,
    ]

    env = os.environ.copy()
    rq_job: Optional[RQJob] = get_current_job()

    if rq_job is not None:
        env["AI_RQ_JOB_ID"] = rq_job.get_id()

    log: BoundLogger = LOGGER.new(rq_job_id=env.get("AI_RQ_JOB_ID"))

    if entry_point_kwargs is not None:
        cmd.extend(shlex.split(entry_point_kwargs))

    with TemporaryDirectory(dir=os.getenv("AI_WORKDIR")) as tmpdir:
        log.info("Executing MLFlow job", cmd=" ".join(cmd))
        p = subprocess.run(args=cmd, cwd=tmpdir, env=env)

    if p.returncode > 0:
        log.warning(
            "MLFlow job stopped unexpectedly", returncode=p.returncode, stderr=p.stderr
        )

    return p
