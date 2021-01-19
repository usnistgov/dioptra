#!/usr/bin/env python
import os

from mlflow.cli import cli as mlflow_cli

from mitre.securingai.sdk.logging import (
    attach_stdout_stream_handler,
    configure_structlog,
    set_logging_level,
)

if __name__ == "__main__":
    attach_stdout_stream_handler(
        True if os.getenv("AI_MLFLOW_RUN_LOG_AS_JSON") else False,
    )
    set_logging_level(os.getenv("AI_MLFLOW_RUN_LOG_LEVEL", default="INFO"))
    configure_structlog()
    mlflow_cli()
