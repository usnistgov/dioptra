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
