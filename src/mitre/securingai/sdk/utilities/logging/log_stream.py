# The LogStream class is adapted from the following source:
#
#     J. Paton, "Redirect standard out to Python’s logging module with contextlib,"
#         John Paton, May 22, 2019. https://johnpaton.net/posts/redirect-logging/
#         (accessed Jan. 18, 2021).

import contextlib
import logging
from abc import ABCMeta, abstractmethod


class LogStream(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, as_json: bool) -> None:
        pass

    def write(self, msg):
        if msg and not msg.isspace():
            self.logger.log(self.level, self._format_newlines(msg))

    def close(self):
        pass

    def flush(self):
        pass

    def _format_newlines(self, msg):
        if self._as_json:
            return "\n".join([x.rstrip() for x in msg.rstrip().splitlines()])

        return "||".join([x.rstrip() for x in msg.rstrip().splitlines()])

    def __enter__(self):
        self._redirector.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._redirector.__exit__(exc_type, exc_value, traceback)


class StdoutLogStream(LogStream):
    def __init__(self, as_json: bool):
        self.logger = logging.getLogger("STDOUT")
        self.name = self.logger.name
        self.level = logging.INFO
        self._as_json = as_json
        self._redirector = contextlib.redirect_stdout(self)  # type: ignore


class StderrLogStream(LogStream):
    def __init__(self, as_json: bool):
        self.logger = logging.getLogger("STDERR")
        self.name = self.logger.name
        self.level = logging.ERROR
        self._as_json = as_json
        self._redirector = contextlib.redirect_stderr(self)  # type: ignore
