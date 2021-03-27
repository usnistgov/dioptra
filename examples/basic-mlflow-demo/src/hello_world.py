#!/usr/bin/env python

import warnings

warnings.filterwarnings("ignore")

import click
import mlflow
import mlflow.tensorflow
import structlog
from log import configure_stdlib_logger, configure_structlog_logger
from prefect import Flow, Parameter, task

from mitre.securingai.sdk.exceptions import TensorflowDependencyError

LOGGER = structlog.get_logger()

# Load pretrained model and test against input dataset.
@click.command()
@click.option(
    "--output-log-string",
    type=click.STRING,
    default="Hello World",
    help="Basic MLflow string input.",
)
def hello_world(output_log_string):
    with mlflow.start_run() as active_run:  # noqa: F841
        flow: Flow = init_hello_world_flow()
        state = flow.run(
            parameters=dict(entry_point="hello_world", log_output=output_log_string)
        )


@task
@require_package("tensorflow", exc_type=TensorflowDependencyError)
def log_parameters(entry_point, log_output):
    LOGGER.info(
        "Execute MLFlow entry point",
        entry_point=entry_point,
        log_output=log_output,
    )


def init_hello_world_flow() -> Flow:
    with Flow("Introduction") as flow:
        (entry_point, log_output,) = (
            Parameter("entry_point"),
            Parameter("log_output"),
        )
        log_parameters(entry_point, log_output)
    return flow


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")
    hello_world()
