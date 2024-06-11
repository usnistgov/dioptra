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
#
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

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
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

    def close(self):
        pass

    def flush(self):
        pass


class StderrLogStream(LogStream):
    def __init__(self, as_json: bool):
        self.logger = logging.getLogger("STDERR")
        self.name = self.logger.name
        self.level = logging.INFO
        self._as_json = as_json
        self._redirector = contextlib.redirect_stderr(self)  # type: ignore

    def close(self):
        pass

    def flush(self):
        pass
