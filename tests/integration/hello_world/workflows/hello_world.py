#!/usr/bin/env python
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

import click
import mlflow
import structlog
from prefect import Flow, Parameter
from prefect.utilities.logging import get_logger as get_prefect_logger
from structlog.stdlib import BoundLogger

from mitre.securingai import pyplugs
from mitre.securingai.sdk.utilities.contexts import plugin_dirs
from mitre.securingai.sdk.utilities.logging import (
    StderrLogStream,
    StdoutLogStream,
    attach_stdout_stream_handler,
    clear_logger_handlers,
    configure_structlog,
    set_logging_level,
)

_PLUGINS_IMPORT_PATH: str = "securingai_builtins"
LOGGER: BoundLogger = structlog.stdlib.get_logger()


@click.command()
@click.option(
    "--metric-first-record",
    type=click.FLOAT,
    default=1.0,
)
@click.option(
    "--metric-second-record",
    type=click.FLOAT,
    default=0.5,
)
def hello_world(metric_first_record, metric_second_record):
    with mlflow.start_run() as active_run:  # noqa: F841
        flow: Flow = init_flow()
        state = flow.run(
            parameters=dict(
                metric_first_record=metric_first_record,
                metric_second_record=metric_second_record,
            )
        )

    return state


def init_flow() -> Flow:
    with Flow("Hello World") as flow:
        metric_first_record, metric_second_record = (
            Parameter("metric_first_record"),
            Parameter("metric_second_record"),
        )

        log_metric_first_record_result = pyplugs.call_task(
            f"{_PLUGINS_IMPORT_PATH}.tracking",
            "mlflow",
            "log_metrics",
            metrics=dict(tracked_metric=metric_first_record),
        )

        log_metric_second_record_result = pyplugs.call_task(  # noqa: F841
            f"{_PLUGINS_IMPORT_PATH}.tracking",
            "mlflow",
            "log_metrics",
            metrics=dict(tracked_metric=metric_second_record),
            upstream_tasks=[log_metric_first_record_result],
        )

    return flow


if __name__ == "__main__":
    log_level: str = os.getenv("AI_JOB_LOG_LEVEL", default="INFO")
    as_json: bool = True if os.getenv("AI_JOB_LOG_AS_JSON") else False

    clear_logger_handlers(get_prefect_logger())
    attach_stdout_stream_handler(as_json)
    set_logging_level(log_level)
    configure_structlog()

    with plugin_dirs(), StdoutLogStream(as_json), StderrLogStream(as_json):
        _ = hello_world()
