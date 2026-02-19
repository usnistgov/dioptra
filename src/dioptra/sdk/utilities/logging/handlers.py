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
import logging.handlers
from typing import Any, Protocol


class JobLogSender(Protocol):
    def __call__(self, job_id: str | int, logs: list[dict[str, str]]) -> Any:
        """
        Add log records for the given job. Job records are dicts of the form::

            {
                "severity": "WARNING",
                "loggerName": "hello_world.tasks",
                "message": "Log message",
            }

        Legal values for severity include DEBUG, INFO, WARNING, ERROR, CRITICAL. The
        logger name captures the name of the logger that emitted the record.

        Args:
            job_id: The resource ID of a job.
            logs: An iterable of log records.
        """
        ...


class DioptraJobLoggingHandler(logging.handlers.BufferingHandler):
    """
    A handler class which buffers job log records in memory, periodically flushing them
    using a sender to route the messages to the appropriate endpoint. Flushing occurs
    whenever the buffer is full, or when an event of a certain severity or greater is
    seen.
    """

    def __init__(
        self,
        sender: JobLogSender,
        job_id: str | int,
        capacity: int = 10,
        flushLevel: int = logging.ERROR,
    ) -> None:
        """
        Initialize this logging handler.

        Args:
            sender: A callable that sends log records to a Dioptra job.
            job_id: The job ID to associate with the logs.
            capacity: The maximum number of records to buffer before flushing.
            flushLevel: The logging level at which to flush the buffer.
        """
        super().__init__(capacity)
        self.sender = sender
        self.job_id = job_id
        self.flushLevel = flushLevel

    def shouldFlush(self, record: logging.LogRecord) -> bool:
        """
        Check for buffer full or a record at the flushLevel or higher.
        """
        return (len(self.buffer) >= self.capacity) or (
            record.levelno >= self.flushLevel
        )

    def flush(self) -> None:
        """
        For the DioptraJobLoggingHandler, flushing means just sending the buffered
        records to the sender.
        """
        self.acquire()
        try:
            if self.buffer:
                self._send_buffered_logs()

            self.buffer.clear()

        finally:
            self.release()

    def close(self) -> None:
        """
        Flush, if appropriately configured, and lose the buffer.
        """
        try:
            self.flush()

        finally:
            self.acquire()
            try:
                super().close()

            finally:
                self.release()

    def _send_buffered_logs(self) -> None:
        try:
            self.sender(job_id=self.job_id, logs=self._extract_logs_from_buffer())

        except Exception:
            for record in self.buffer:
                self.handleError(record)

    def _extract_logs_from_buffer(self) -> list[dict[str, str]]:
        return [
            {
                "severity": record.levelname,
                "loggerName": record.name,
                "message": self.format(record),
            }
            for record in self.buffer
        ]
