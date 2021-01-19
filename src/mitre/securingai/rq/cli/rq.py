#!/usr/bin/env python
import os

from rq.cli.cli import main as rq_cli

from mitre.securingai.sdk.logging import attach_stdout_stream_handler, set_logging_level

if __name__ == "__main__":
    attach_stdout_stream_handler(
        True if os.getenv("AI_RQ_WORKER_LOG_AS_JSON") else False,
    )
    set_logging_level(os.getenv("AI_RQ_WORKER_LOG_LEVEL", default="INFO"))
    rq_cli()
