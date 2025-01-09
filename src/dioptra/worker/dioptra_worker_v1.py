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
"""
A CLI tool used to start up a worker process for running jobs.
"""

import logging
import os
import sys

import rq.cli

from dioptra.sdk.utilities.logging import (
    attach_stdout_stream_handler,
    set_logging_level,
)

_REQUIRED_ENV = {
    "MLFLOW_S3_ENDPOINT_URL",
    "DIOPTRA_API",
    "DIOPTRA_WORKER_USERNAME",
    "DIOPTRA_WORKER_PASSWORD",
}


def _setup_logging() -> None:
    attach_stdout_stream_handler(
        True if os.getenv("DIOPTRA_RQ_WORKER_LOG_AS_JSON") else False,
    )
    set_logging_level(os.getenv("DIOPTRA_RQ_WORKER_LOG_LEVEL", default="INFO"))


def main() -> int:
    _setup_logging()
    log = logging.getLogger("dioptra-worker")
    exit_status = 0

    # We know what functions will be executed through rq and what they
    # require, so we may as well check that before starting up the worker.
    # Better to error out as early as possible.
    unset_vars = _REQUIRED_ENV - os.environ.keys()
    if unset_vars:
        exit_status = 1
        log.fatal("Environment variables must be set: %s", ", ".join(unset_vars))
    else:
        # Disabling standalone mode means the worker function can return a
        # value to this script, exceptions will propagate to us, etc. (as
        # opposed to being intercepted and handled by click).  As a wrapper
        # that seems appropriate, although I don't think the worker function
        # is written to return anything, and we presently don't need to
        # specially handle any of the exceptions.
        rq.cli.worker(standalone_mode=False)

    return exit_status


if __name__ == "__main__":
    sys.exit(main())
