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

import logging
import re
import urllib.parse
from typing import Final

CLIENT_SESSIONS_MODULE: Final[str] = "dioptra.client.sessions"
JOB_LOG_PATH_RE: Final = re.compile(r"^/api/v1/jobs/\d+/log/?$")


class LibraryFilter(logging.Filter):
    """Filter to disallow log records based on the logger name."""

    def __init__(self, library_names: list[str]) -> None:
        """Initialize the filter.

        Args:
            library_names: A list of library names to filter out.
        """
        super().__init__()
        self.library_names = library_names

    def filter(self, record: logging.LogRecord) -> bool:
        """Determine if the specified record is to be logged.

        Returns True if the record should be logged, or False otherwise. If deemed
        appropriate, the record may be modified in-place.
        """
        # Allow the log record if its logger name is NOT in the specified libraries
        return not any(
            record.name.startswith(lib_name) for lib_name in self.library_names
        )


class OmitClientJobLoggingFilter(logging.Filter):
    """
    Filter to omit specific log records related to forwarding job logs to the Dioptra
    API.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Determine if the specified record is to be logged.

        Returns True if the record should be logged, or False otherwise. If deemed
        appropriate, the record may be modified in-place.
        """
        # Allow the log record if its logger name is NOT associated with the client
        # sessions module
        if not record.name.startswith(CLIENT_SESSIONS_MODULE):
            return True

        # Allow the log record if it's not at the DEBUG level
        if record.levelno != logging.DEBUG:
            return True

        # Allow the log record if it is not a general request or response log
        message = record.getMessage()
        if not message.startswith("Request made:") and not message.startswith(
            "Response received:"
        ):
            return True

        # Allow the log record if it doesn't have positional arguments (the args
        # attribute is not a tuple)
        args = record.args
        if not isinstance(args, tuple):
            return True

        # Allow the log record if it has less than 2 positional arguments
        if len(args) < 2:
            return True

        # Allow the log record if it is not a POST request
        url, method = args[:2]
        if str(method) != "POST":
            return True

        # Allow the log record if the target URL is not the job logging endpoint
        endpoint_path = urllib.parse.urlparse(str(url)).path
        if not JOB_LOG_PATH_RE.match(endpoint_path):
            return True

        # The log record is a request/response message emitted when the DioptraClient is
        # forwarding a log to the /api/v1/jobs/{id}/log endpoint. We need to filter it
        # out to prevent recursion.
        return False
