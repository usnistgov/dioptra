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
"""The module defining the endpoints for Plugin resources."""

import uuid
from urllib.parse import unquote

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.routes import V1_JOBS_ROUTE
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.schemas import IdStatusResponseSchema
from dioptra.restapi.v1.shared.snapshots.controller import (
    generate_resource_snapshots_endpoint,
    generate_resource_snapshots_id_endpoint,
)
from dioptra.restapi.v1.shared.tags.controller import (
    generate_resource_tags_endpoint,
    generate_resource_tags_id_endpoint,
)
from dioptra.restapi.v1.workflows.lib.export_job_parameters import (
    build_job_artifacts_dict,
    build_job_parameters_dict,
)

from .schema import (
    JobGetQueryParameters,
    JobMlflowRunSchema,
    JobPageSchema,
    JobSchema,
    JobStatusSchema,
    MetricsSchema,
    MetricsSnapshotPageSchema,
    MetricsSnapshotsGetQueryParameters,
)
from .service import (
    RESOURCE_TYPE,
    SEARCHABLE_FIELDS,
    JobIdMetricsService,
    JobIdMetricsSnapshotsService,
    JobIdMlflowrunService,
    JobIdService,
    JobIdStatusService,
    JobService,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Job", description="Job endpoint")


@api.route("/")
class JobEndpoint(Resource):
    @inject
    def __init__(self, job_service: JobService, *args, **kwargs) -> None:
        """Initialize the jobs resource.

        All arguments are provided via dependency injection.

        Args:
            job_service: A JobService object.
        """
        self._job_service = job_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=JobGetQueryParameters, api=api)
    @responds(schema=JobPageSchema, api=api)
    def get(self):
        """Gets a list of all Job resources."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Job", request_type="GET"
        )
        log.debug("Request received")
        parsed_query_params = request.parsed_query_params  # noqa: F841

        group_id = parsed_query_params["group_id"]
        search_string = unquote(parsed_query_params["search"])
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]
        sort_by_string = parsed_query_params["sort_by"]
        descending = parsed_query_params["descending"]

        jobs, total_num_jobs = self._job_service.get(
            group_id=group_id,
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
            sort_by_string=sort_by_string,
            descending=descending,
            log=log,
        )
        return utils.build_paging_envelope(
            "jobs",
            build_fn=utils.build_job,
            data=jobs,
            group_id=group_id,
            query=search_string,
            draft_type=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_jobs,
            sort_by=sort_by_string,
            descending=descending,
        )


@api.route("/<int:id>")
@api.param("id", "ID for the Job resource.")
class JobIdEndpoint(Resource):
    @inject
    def __init__(self, job_id_service: JobIdService, *args, **kwargs) -> None:
        """Initialize the jobs resource.

        All arguments are provided via dependency injection.

        Args:
            job_id_service: A JobIdService object.
        """
        self._job_id_service = job_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=JobSchema, api=api)
    def get(self, id: int):
        """Gets a Job resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Job", request_type="GET", id=id
        )
        return utils.build_job(self._job_id_service.get(id, log=log))

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int):
        """Deletes a Job resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Job", request_type="DELETE", id=id
        )
        return self._job_id_service.delete(job_id=id, log=log)


@api.route("/<int:id>/parameters")
@api.param("id", "ID for the Job resource.")
class JobIdParametersEndpoint(Resource):
    @inject
    def __init__(self, job_id_service: JobIdService, *args, **kwargs) -> None:
        """Initialize the jobs resource.

        All arguments are provided via dependency injection.

        Args:
            job_id_service: A JobIdService object.
        """
        self._job_id_service = job_id_service
        super().__init__(*args, **kwargs)

    @login_required
    def get(self, id: int):
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Job", request_type="GET", id=id
        )
        return build_job_parameters_dict(
            job_param_values=self._job_id_service.get_parameter_values(id),
            logger=log,
        )


@api.route("/<int:id>/artifactParameters")
@api.param("id", "ID for the Job resource.")
class JobIdArtifactParametersEndpoint(Resource):
    @inject
    def __init__(self, job_id_service: JobIdService, *args, **kwargs) -> None:
        """Initialize the jobs resource.

        All arguments are provided via dependency injection.

        Args:
            job_id_service: A JobIdService object.
        """
        self._job_id_service = job_id_service
        super().__init__(*args, **kwargs)

    @login_required
    def get(self, id: int):
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Job", request_type="GET", id=id
        )
        return build_job_artifacts_dict(
            job_artifact_values=self._job_id_service.get_artifact_values(id),
            logger=log,
        )


@api.route("/<int:id>/status")
@api.param("id", "ID for the Job resource.")
class JobIdStatusEndpoint(Resource):
    @inject
    def __init__(
        self, job_id_status_service: JobIdStatusService, *args, **kwargs
    ) -> None:
        """Initialize the jobs resource.

        All arguments are provided via dependency injection.

        Args:
            job_id_service: A JobIdStatusService object.
        """
        self._job_id_status_service = job_id_status_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=JobStatusSchema, api=api)
    def get(self, id: int):
        """Gets a Job resource's status."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Job", request_type="GET", id=id
        )
        return self._job_id_status_service.get(
            job_id=id, error_if_not_found=True, log=log
        )


@api.route("/<int:id>/mlflowRun")
@api.param("id", "ID for the Job resource.")
class JobIdMlflowrunEndpoint(Resource):
    @inject
    def __init__(
        self,
        job_id_mlflowrun_service: JobIdMlflowrunService,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the jobs resource.

        All arguments are provided via dependency injection.

        Args:
            job_id_service: A JobIdMlflowrunService object.
        """
        self._job_id_mlflowrun_service = job_id_mlflowrun_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=JobMlflowRunSchema, api=api)
    def get(self, id: int):
        """Gets a Job resource's mlflow run id."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="JobIdMlflowrunEndpoint",
            request_type="GET",
            job_id=id,
        )
        return {"mlflow_run_id": self._job_id_mlflowrun_service.get(job_id=id, log=log)}

    @login_required
    @accepts(schema=JobMlflowRunSchema, api=api)
    @responds(schema=JobMlflowRunSchema, api=api)
    def post(self, id: int):
        """Sets the mlflow run id for a Job"""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="JobIdMlflowrunEndpoint",
            request_type="POST",
            job_id=id,
        )
        parsed_obj = request.parsed_obj  # type: ignore
        return self._job_id_mlflowrun_service.create(
            job_id=id,
            mlflow_run_id=parsed_obj["mlflow_run_id"],
            error_if_not_found=True,
            log=log,
        )


@api.route("/<int:id>/metrics")
@api.param("id", "ID for the Job resource.")
class JobIdMetricsEndpoint(Resource):
    @inject
    def __init__(
        self,
        job_id_metrics_service: JobIdMetricsService,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the jobs resource.

        All arguments are provided via dependency injection.

        Args:
            job_id_metrics_service: A JobIdMetricsService object.
        """
        self._job_id_metrics_service = job_id_metrics_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=MetricsSchema(many=True), api=api)
    def get(self, id: int):
        """Gets a Job resource's latest metrics."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="JobIdMetricsEndpoint",
            request_type="GET",
            job_id=id,
        )

        return self._job_id_metrics_service.get(
            job_id=id, error_if_not_found=True, log=log
        )

    @login_required
    @accepts(schema=MetricsSchema, api=api)
    @responds(schema=MetricsSchema, api=api)
    def post(self, id: int):
        """Sets a metric for a Job"""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="JobIdMetricsEndpoint",
            request_type="POST",
            job_id=id,
        )
        parsed_obj = request.parsed_obj  # type: ignore
        return self._job_id_metrics_service.update(
            job_id=id,
            metric_name=parsed_obj["name"],
            metric_value=parsed_obj["value"],
            metric_step=parsed_obj["step"],
            error_if_not_found=True,
            log=log,
        )


@api.route("/<int:id>/metrics/<string:name>/snapshots")
@api.param("id", "ID for the Job resource.")
@api.param("name", "Name of the metric.")
class JobIdMetricsSnapshotsEndpoint(Resource):
    @inject
    def __init__(
        self,
        job_id_metrics_snapshots_service: JobIdMetricsSnapshotsService,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the jobs resource.

        All arguments are provided via dependency injection.

        Args:
            job_id_metrics_snapshots_service: A JobIdMetricsSnapshotsService object.
        """
        self._job_id_metrics_snapshots_service = job_id_metrics_snapshots_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=MetricsSnapshotsGetQueryParameters, api=api)
    @responds(schema=MetricsSnapshotPageSchema, api=api)
    def get(self, id: int, name: str):
        """Gets a Job resource's metric history."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="JobIdMetricsSnapshotsEndpoint",
            request_type="GET",
            job_id=id,
            metric_name=name,
        )
        parsed_query_params = request.parsed_query_params  # type: ignore
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]
        metrics_page, total_num_metrics = self._job_id_metrics_snapshots_service.get(
            job_id=id,
            metric_name=name,
            page_index=page_index,
            page_length=page_length,
            error_if_not_found=True,
            log=log,
        )

        return utils.build_paging_envelope(
            f"jobs/{id}/metrics/{name}/snapshots",
            build_fn=utils.build_metrics_snapshots,
            data=metrics_page,
            group_id=None,
            query=None,
            draft_type=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_metrics,
            sort_by=None,
            descending=None,
        )


JobSnapshotsResource = generate_resource_snapshots_endpoint(
    api=api,
    resource_model=models.Job,
    resource_name=RESOURCE_TYPE.get_db_schema_name(),
    route_prefix=V1_JOBS_ROUTE,
    searchable_fields=SEARCHABLE_FIELDS,
    page_schema=JobPageSchema,
    build_fn=utils.build_job,
)
JobSnapshotsIdResource = generate_resource_snapshots_id_endpoint(
    api=api,
    resource_model=models.Job,
    resource_name=RESOURCE_TYPE.get_db_schema_name(),
    response_schema=JobSchema,
    build_fn=utils.build_job,
)

JobTagsResource = generate_resource_tags_endpoint(
    api=api,
    resource_name=RESOURCE_TYPE.get_db_schema_name(),
)
JobTagsIdResource = generate_resource_tags_id_endpoint(
    api=api,
    resource_name=RESOURCE_TYPE.get_db_schema_name(),
)
