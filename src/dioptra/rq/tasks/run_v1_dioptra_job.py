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
import tempfile

import structlog
from structlog.stdlib import BoundLogger

import dioptra.sdk.utilities.run_dioptra_job as run_dioptra_job
from dioptra.sdk.utilities.paths import set_cwd

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def run_v1_dioptra_job(job_id: int, experiment_id: int) -> None:  # noqa: C901
    """Sets-up a temporary directory and starts a Dioptra job

    Args:
        job_id: The Dioptra job ID.
        experiment_id: The Dioptra experiment ID.
    """
    log = LOGGER.new(job_id=job_id, experiment_id=experiment_id)  # noqa: F841

    # Set up a temporary directory and set it as the current working directory
    with tempfile.TemporaryDirectory() as tempdir, set_cwd(tempdir):
        run_dioptra_job.main(
            job_id=job_id,
            experiment_id=experiment_id,
            logger=log,
        )
