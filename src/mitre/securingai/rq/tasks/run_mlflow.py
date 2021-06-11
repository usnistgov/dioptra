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
import os
import shlex
import subprocess
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
from typing import List, Optional

import structlog
from rq.job import Job as RQJob
from rq.job import get_current_job
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()


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
