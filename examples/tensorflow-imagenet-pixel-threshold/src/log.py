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
import datetime
import logging
import sys

import structlog
from pythonjsonlogger import jsonlogger


def configure_stdlib_logger(level, log_filepath):
    root_logger: logging.Logger = logging.getLogger()
    level: str = _get_logging_level(level.strip().upper())

    if log_filepath is None:
        handler = logging.StreamHandler(sys.stdout)

    else:
        handler = logging.FileHandler(log_filepath)
        handler.setFormatter(jsonlogger.JsonFormatter())

    root_logger.addHandler(handler)
    root_logger.setLevel(level)


def configure_structlog_logger(fmt):
    processors = _set_structlog_processors(fmt=fmt)

    structlog.configure_once(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def _add_timestamp(_, __, event_dict: dict) -> dict:
    now = datetime.datetime.utcnow()
    millis = "{:3d}".format(int(now.microsecond / 1000))
    event_dict["timestamp"] = "%s.%sZ" % (now.strftime("%Y-%m-%dT%H:%M:%S"), millis)

    return event_dict


def _get_logging_level(level):
    allowed_levels = {"DEBUG", "ERROR", "INFO", "WARNING"}

    if level not in allowed_levels:
        level = "INFO"

    return level


def _set_structlog_processors(fmt):
    if fmt == "json":
        return [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            _add_timestamp,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.render_to_log_kwargs,
        ]

    return [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S.%f"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(),
    ]
