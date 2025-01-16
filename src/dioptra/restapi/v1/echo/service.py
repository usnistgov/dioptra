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
import os

import structlog
from structlog.stdlib import BoundLogger
from werkzeug.datastructures import FileStorage

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class EchoService(object):
    def create(
        self,
        test_files: list[FileStorage],
        test_string: str,
        **kwargs,
    ):
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        test_files_info = [
            {"filename": x.filename, "size": x.stream.seek(0, os.SEEK_END)}
            for x in test_files
        ]
        log.info("Echo service called", test_files_info=test_files_info)
        return {"test_files_info": test_files_info, "test_string": test_string or ""}


class EchoSingleFileService(object):
    def create(
        self,
        test_file: FileStorage | None,
        test_string: str,
        **kwargs,
    ):
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        response = {"test_string": test_string or "", "test_file_info": {}}

        if test_file:
            response["test_file_info"] = {
                "filename": test_file.filename,
                "size": test_file.stream.seek(0, os.SEEK_END),
            }

        log.info(
            "Echo Single File service called",
            test_file_info=response["test_file_info"],
            test_string=response["test_string"],
        )
        return response
