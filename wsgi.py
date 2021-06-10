# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
import os

from mitre.securingai.restapi import create_app

from mitre.securingai.sdk.utilities.logging import (
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
