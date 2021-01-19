import os

from mitre.securingai.restapi import create_app

from mitre.securingai.sdk.logging import (
    attach_stdout_stream_handler,
    configure_structlog,
    set_logging_level,
)


attach_stdout_stream_handler(
    True if os.getenv("AI_RESTAPI_LOG_AS_JSON") else False,
)
set_logging_level(os.getenv("AI_RESTAPI_LOG_LEVEL", default="INFO"))
configure_structlog()
app = create_app(env=os.getenv("AI_RESTAPI_ENV"))
