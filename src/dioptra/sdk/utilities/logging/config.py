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
import logging
import sys
from collections.abc import Iterator, Mapping, MutableMapping
from contextlib import contextmanager
from logging import getLogger
from typing import Any, Callable

import structlog

from dioptra.client import DioptraClient
from dioptra.client.base import DioptraResponseProtocol
from dioptra.sdk.utilities.auth_client import get_authenticated_worker_client

from .filters import LibraryFilter, OmitClientJobLoggingFilter
from .handlers import DioptraJobLoggingHandler

ProcessorType = Callable[
    [Any, str, MutableMapping[str, Any]],
    Mapping[str, Any] | str | bytes | tuple[Any, ...],
]


def attach_stdout_stream_handler(
    as_json: bool, logger: logging.Logger | None = None
) -> None:
    logger = logger or getLogger()
    log_processor: ProcessorType = _get_structlog_processor(as_json)

    handler = logging.StreamHandler(sys.stdout)
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=log_processor,
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
    handler.setFormatter(formatter)
    logging.captureWarnings(True)
    logger.addHandler(handler)


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
    client = client or get_authenticated_worker_client(logger, "response")

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


def clear_logger_handlers(logger: logging.Logger | None) -> None:
    if logger is None:
        return None

    for handler in logger.handlers:
        logger.removeHandler(handler)


def configure_structlog_for_worker() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def configure_structlog() -> None:
    processors: list[Any] = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ]

    structlog.configure_once(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def set_logging_level(level: str, logger: logging.Logger | None = None) -> None:
    logger = logger or getLogger()
    logger.setLevel(_get_logging_level(level.strip().upper()))


def _get_structlog_processor(as_json: bool) -> ProcessorType:
    if as_json:
        log_processor: ProcessorType = structlog.processors.JSONRenderer()
        return log_processor

    log_processor = structlog.dev.ConsoleRenderer()
    return log_processor


def _get_logging_level(level: str) -> str:
    allowed_levels = {"DEBUG", "ERROR", "INFO", "WARNING"}

    if level not in allowed_levels:
        level = "INFO"

    return level
