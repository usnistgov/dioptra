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
"""The server-side functions that perform workflows endpoint operations."""
from typing import IO, Any, Final, List

import structlog
from structlog.stdlib import BoundLogger

from dioptra.restapi.v1.lib.signature_analysis import get_plugin_signatures

from .lib import views
from .lib.package_job_files import package_job_files
from .schema import FileTypes

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "workflow"


class JobFilesDownloadService(object):
    """The service methods for packaging job files for download."""

    def get(self, job_id: int, file_type: FileTypes, **kwargs) -> IO[bytes]:
        """Get the files needed to run a job and package them for download.

        Args:
            job_id: The identifier of the job.
            file_type: The type of file to package the job files into. Must be one of
                the values in the FileTypes enum.

        Returns:
            The packaged job files returned as a named temporary file.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get job files download", job_id=job_id, file_type=file_type)

        experiment = views.get_experiment(job_id=job_id, logger=log)
        entry_point = views.get_entry_point(job_id=job_id, logger=log)
        entry_point_plugin_files = views.get_entry_point_plugin_files(
            job_id=job_id, logger=log
        )
        job_parameter_values = views.get_job_parameter_values(job_id=job_id, logger=log)
        plugin_parameter_types = views.get_plugin_parameter_types(
            job_id=job_id, logger=log
        )
        return package_job_files(
            job_id=job_id,
            experiment=experiment,
            entry_point=entry_point,
            entry_point_plugin_files=entry_point_plugin_files,
            job_parameter_values=job_parameter_values,
            plugin_parameter_types=plugin_parameter_types,
            file_type=file_type,
            logger=log,
        )


class SignatureAnalysisService(object):
    """The service methods for performing signature analysis on a file."""

    def post(
        self, filename: str, fileContents: str, **kwargs
    ) -> dict[str, List[dict[str, Any]]]:
        """Perform signature analysis on a file.

        Args:
            filename: The name of the file.
            file_contents: The contents of the file.

        Returns:
            A dictionary containing the signature analysis.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Performing signature analysis",
            filename=filename,
            python_source=fileContents,
        )

        signatures = list(
            get_plugin_signatures(
                python_source=fileContents,
                filepath=filename,
            )
        )

        endpoint_analyses = []
        for signature in signatures:
            function_name = signature["name"]
            function_inputs = signature["inputs"]
            function_outputs = signature["outputs"]
            inferences = signature["suggested_types"]
            endpoint_analysis = {}

            endpoint_analysis["name"] = function_name
            endpoint_analysis["inputs"] = function_inputs
            endpoint_analysis["outputs"] = function_outputs

            # Compute the suggestions for the unknown types

            missing_types = []

            for inference in inferences:
                suggested_type = inference[
                    "suggestion"
                ]  # replace this with resource id's for suggestions
                original_annotation = inference[
                    "type_annotation"
                ]  # do a database lookup with this
                missing_types += [
                    {
                        "annotation": original_annotation,
                        "missing_type": suggested_type,
                    }
                ]

            endpoint_analysis["missing_types"] = missing_types
            endpoint_analyses += [endpoint_analysis]
        return {"plugins": endpoint_analyses}
