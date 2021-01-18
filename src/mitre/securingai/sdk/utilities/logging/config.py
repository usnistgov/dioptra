import logging
import sys
from logging import getLogger
from typing import Any, Callable, List, Mapping, MutableMapping, Optional, Tuple, Union

import structlog

ProcessorType = Callable[
    [Any, str, MutableMapping[str, Any]],
    Union[Mapping[str, Any], str, bytes, Tuple[Any, ...]],
]


def attach_stdout_stream_handler(
    as_json: bool, logger: Optional[logging.Logger] = None
) -> None:
    logger = logger or getLogger()
    log_processor: ProcessorType = _get_structlog_processor(as_json)

    handler = logging.StreamHandler(sys.stdout)
    formatter = structlog.stdlib.ProcessorFormatter(
        processor=log_processor,
        foreign_pre_chain=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ],
    )
    handler.setFormatter(formatter)
    logging.captureWarnings(True)
    logger.addHandler(handler)


def clear_logger_handlers(logger: Optional[logging.Logger]) -> None:
    if logger is None:
        return None

    for handler in logger.handlers:
        logger.removeHandler(handler)


def configure_structlog() -> None:
    processors: List[Any] = [
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


def set_logging_level(level: str, logger: Optional[logging.Logger] = None) -> None:
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
