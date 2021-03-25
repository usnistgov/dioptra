#!/usr/bin/env python

import warnings

warnings.filterwarnings("ignore")

import click
import mlflow
import mlflow.tensorflow
import structlog
from log import configure_stdlib_logger, configure_structlog_logger

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
    with mlflow.start_run() as _:
        LOGGER.info(
            "Execute MLFlow entry point",
            entry_point="hello_world",
            log_output=output_log_string,
        )


if __name__ == "__main__":
    configure_stdlib_logger("INFO", log_filepath=None)
    configure_structlog_logger("console")
    hello_world()
