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
from collections.abc import Iterator
from contextlib import contextmanager
from logging import getLogger

import structlog

from dioptra.client import DioptraClient
from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.worker import get_authenticated_worker_client

from .filters import LibraryFilter, OmitClientJobLoggingFilter
from .handlers import DioptraJobLoggingHandler


@contextmanager
def forward_job_logs_to_api(
    job_id: str | int, client: DioptraClient[DioptraResponseProtocol] | None = None
) -> Iterator[None]:
    """Context manager for forwarding job logs to the Dioptra API.

    Args:
        job_id: The Dioptra job ID the logs are for.
        client: An authenticated Dioptra client. If not provided, it will be created
            using environment variables for authentication.
    """
    logger = getLogger()
    if client is None:
        client = get_authenticated_worker_client(logger, "response")

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.dev.ConsoleRenderer(colors=False),
        ],
        foreign_pre_chain=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ],
    )
    library_filter = LibraryFilter(["git", "rq", "urllib3", "tests"])
    omit_client_job_logging_filter = OmitClientJobLoggingFilter()

    handler = DioptraJobLoggingHandler(
        sender=client.jobs.append_logs_by_id, job_id=job_id
    )
    handler.setFormatter(formatter)
    handler.addFilter(library_filter)
    handler.addFilter(omit_client_job_logging_filter)

    try:
        logger.addHandler(handler)
        yield

    finally:
        handler.close()
        logger.removeHandler(handler)
