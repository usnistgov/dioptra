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
"""The module defining the endpoints for Experiment resources."""
import uuid
from typing import cast
from urllib.parse import unquote

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.routes import V1_EXPERIMENTS_ROUTE
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.artifacts.schema import ArtifactSchema
from dioptra.restapi.v1.artifacts.service import JobArtifactService
from dioptra.restapi.v1.entrypoints.schema import EntrypointRefSchema
from dioptra.restapi.v1.jobs.schema import (
    ExperimentJobGetQueryParameters,
    JobMlflowRunSchema,
    JobPageSchema,
    JobSchema,
    JobStatusSchema,
)
from dioptra.restapi.v1.jobs.service import (
    ExperimentJobIdMlflowrunService,
    ExperimentJobIdService,
    ExperimentJobIdStatusService,
    ExperimentJobService,
)
from dioptra.restapi.v1.schemas import IdListSchema, IdStatusResponseSchema
from dioptra.restapi.v1.shared.drafts.controller import (
    generate_resource_drafts_endpoint,
    generate_resource_drafts_id_endpoint,
    generate_resource_id_draft_endpoint,
)
from dioptra.restapi.v1.shared.snapshots.controller import (
    generate_resource_snapshots_endpoint,
    generate_resource_snapshots_id_endpoint,
)
from dioptra.restapi.v1.shared.tags.controller import (
    generate_resource_tags_endpoint,
    generate_resource_tags_id_endpoint,
)

from .schema import (
    ExperimentDraftSchema,
    ExperimentGetQueryParameters,
    ExperimentMutableFieldsSchema,
    ExperimentPageSchema,
    ExperimentSchema,
)
from .service import (
    RESOURCE_TYPE,
    SEARCHABLE_FIELDS,
    ExperimentIdEntrypointsIdService,
    ExperimentIdEntrypointsService,
    ExperimentIdService,
    ExperimentService,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Experiments", description="Experiments endpoint")


@api.route("/")
class ExperimentEndpoint(Resource):
    @inject
    def __init__(self, experiment_service: ExperimentService, *args, **kwargs) -> None:
        """Initialize the experiment resource.

        All arguments are provided via dependency injection.

        Args:
            experiment_service: An ExperimentService object.
        """
        self._experiment_service = experiment_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=ExperimentGetQueryParameters, api=api)
    @responds(schema=ExperimentPageSchema, api=api)
    def get(self):
        """Gets a page of Experiment resources matching the filter parameters."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentEndpoint",
            request_type="GET",
        )
        parsed_query_params = request.parsed_query_params  # noqa: F841

        group_id = parsed_query_params["group_id"]
        search_string = parsed_query_params["search"]
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]

        experiments, total_num_experiments = self._experiment_service.get(
            group_id=group_id,
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
            log=log,
        )
        return utils.build_paging_envelope(
            "experiments",
            build_fn=utils.build_experiment,
            data=experiments,
            group_id=group_id,
            query=search_string,
            draft_type=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_experiments,
        )

    @login_required
    @accepts(schema=ExperimentSchema, api=api)
    @responds(schema=ExperimentSchema, api=api)
    def post(self):
        """Creates an Experiment resource with a provided name."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentEndpoint",
            request_type="POST",
        )
        parsed_obj = request.parsed_obj  # noqa: F841
        experiment = self._experiment_service.create(
            name=parsed_obj["name"],
            description=parsed_obj["description"],
            group_id=parsed_obj["group_id"],
            entrypoint_ids=parsed_obj["entrypoint_ids"],
            log=log,
        )
        return utils.build_experiment(experiment)


@api.route("/<int:id>")
@api.param("id", "ID for the Experiment resource.")
class ExperimentIdEndpoint(Resource):
    @inject
    def __init__(
        self, experiment_id_service: ExperimentIdService, *args, **kwargs
    ) -> None:
        """Initialize the experiment resource.

        All arguments are provided via dependency injection.

        Args:
            experiment_id_service: An ExperimentIdService object.
        """
        self._experiment_id_service = experiment_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=ExperimentSchema, api=api)
    def get(self, id: int):
        """Gets an experiment by its unique identifier."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="Experiment",
            request_type="GET",
            id=id,
        )
        experiment = cast(
            models.Experiment,
            self._experiment_id_service.get(id, error_if_not_found=True, log=log),
        )
        return utils.build_experiment(experiment)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int):
        """Deletes an experiment by its unique identifier."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="Experiment",
            request_type="DELETE",
            id=id,
        )
        return self._experiment_id_service.delete(id, log=log)

    @login_required
    @accepts(schema=ExperimentMutableFieldsSchema, api=api)
    @responds(schema=ExperimentSchema, api=api)
    def put(self, id: int):
        """Modifies an experiment by its unique identifier."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="Experiment",
            request_type="PUT",
            id=id,
        )
        parsed_obj = request.parsed_obj  # type: ignore
        experiment = cast(
            utils.ExperimentDict,
            self._experiment_id_service.modify(
                id,
                name=parsed_obj["name"],
                description=parsed_obj["description"],
                entrypoint_ids=parsed_obj["entrypoint_ids"],
                error_if_not_found=True,
                log=log,
            ),
        )
        return utils.build_experiment(experiment)


@api.route("/<int:id>/jobs")
@api.param("id", "ID for the Experiment resource.")
class ExperimentIdJobEndpoint(Resource):
    @inject
    def __init__(
        self,
        experiment_job_service: ExperimentJobService,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the Job resource.

        All arguments are provided via dependency injection.

        Args:
            experiment_id_job_service: An ExperimentIdJobService object.
        """
        self._experiment_job_service = experiment_job_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(query_params_schema=ExperimentJobGetQueryParameters, api=api)
    @responds(schema=JobPageSchema, api=api)
    def get(self, id: int):
        """Returns a list of jobs for a specified Experiment."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentIdJobEndpoint",
            request_type="GET",
            id=id,
        )
        parsed_query_params = request.parsed_query_params  # type: ignore

        search_string = unquote(parsed_query_params["search"])
        page_index = parsed_query_params["index"]
        page_length = parsed_query_params["page_length"]

        jobs, total_num_jobs = self._experiment_job_service.get(
            experiment_id=id,
            search_string=search_string,
            page_index=page_index,
            page_length=page_length,
            log=log,
        )
        return utils.build_paging_envelope(
            f"experiments/{id}/jobs",
            build_fn=utils.build_job,
            data=jobs,
            group_id=None,
            query=search_string,
            draft_type=None,
            index=page_index,
            length=page_length,
            total_num_elements=total_num_jobs,
        )

    @login_required
    @accepts(schema=JobSchema(exclude=["groupId"]), api=api)
    @responds(schema=JobSchema, api=api)
    def post(self, id: int):
        """Creates a Job resource under the specified Experiment."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentIdJobEndpoint",
            request_type="POST",
        )
        parsed_obj = request.parsed_obj  # type: ignore

        job = self._experiment_job_service.create(
            experiment_id=id,
            queue_id=parsed_obj["queue_id"],
            entrypoint_id=parsed_obj["entrypoint_id"],
            values=parsed_obj["values"],
            description=parsed_obj["description"],
            timeout=parsed_obj["timeout"],
            log=log,
        )
        return utils.build_job(job)


@api.route("/<int:id>/jobs/<int:jobId>")
@api.param("id", "ID for the Experiment resource.")
@api.param("jobId", "ID for the Job resource.")
class ExperimentIdJobIdEndpoint(Resource):
    @inject
    def __init__(
        self, experiment_job_id_service: ExperimentJobIdService, *args, **kwargs
    ) -> None:
        """Initialize the jobs resource.

        All arguments are provided via dependency injection.

        Args:
            job_id_service: A JobIdService object.
        """
        self._experiment_job_id_service = experiment_job_id_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=JobSchema, api=api)
    def get(self, id: int, jobId: int):
        """Gets a Job resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentIdJobIdEndpoint",
            request_type="GET",
            id=id,
            job_id=jobId,
        )
        job = self._experiment_job_id_service.get(id, job_id=jobId, log=log)
        return utils.build_job(job)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int, jobId: int):
        """Deletes a Job resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentIdJobIdEndpoint",
            request_type="DELETE",
            id=id,
            job_id=jobId,
        )
        return self._experiment_job_id_service.delete(id, job_id=jobId, log=log)


@api.route("/<int:id>/jobs/<int:jobId>/status")
@api.param("id", "ID for the Experiment resource.")
@api.param("jobId", "ID for the Job resource.")
class ExperimentIdJobIdStatusEndpoint(Resource):
    @inject
    def __init__(
        self,
        experiment_job_id_status_service: ExperimentJobIdStatusService,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the jobs resource.

        All arguments are provided via dependency injection.

        Args:
            job_id_service: A JobIdStatusService object.
        """
        self._experiment_job_id_status_service = experiment_job_id_status_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=JobStatusSchema, api=api)
    def get(self, id: int, jobId: int):
        """Gets a Job resource's status."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentIdJobIdStatusEndpoint",
            request_type="GET",
            experiment_id=id,
            job_id=jobId,
        )
        return self._experiment_job_id_status_service.get(
            experiment_id=id, job_id=jobId, error_if_not_found=True, log=log
        )

    @login_required
    @accepts(schema=JobStatusSchema, api=api)
    @responds(schema=JobStatusSchema, api=api)
    def put(self, id: int, jobId: int):
        """Modifies a Job resource's status."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentIdJobIdStatusEndpoint",
            request_type="PUT",
            experiment_id=id,
            job_id=jobId,
        )
        parsed_obj = request.parsed_obj  # type: ignore
        return self._experiment_job_id_status_service.modify(
            experiment_id=id,
            job_id=jobId,
            status=parsed_obj["status"],
            error_if_not_found=True,
            log=log,
        )


@api.route("/<int:id>/jobs/<int:jobId>/mlflowRun")
@api.param("id", "ID for the Experiment resource.")
@api.param("jobId", "ID for the Job resource.")
class ExperimentIdJobIdMlflowrunEndpoint(Resource):
    @inject
    def __init__(
        self,
        experiment_job_id_mlflowrun_service: ExperimentJobIdMlflowrunService,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the jobs resource.

        All arguments are provided via dependency injection.

        Args:
            job_id_service: A JobIdStatusService object.
        """
        self._experiment_job_id_mlflowrun_service = experiment_job_id_mlflowrun_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=JobMlflowRunSchema, api=api)
    def get(self, id: int, jobId: int):
        """Gets a Job resource's mlflow run id."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentIdJobIdMlflowrunEndpoint",
            request_type="GET",
            experiment_id=id,
            job_id=jobId,
        )
        return self._experiment_job_id_mlflowrun_service.get(
            experiment_id=id, job_id=jobId, error_if_not_found=True, log=log
        )

    @login_required
    @accepts(schema=JobMlflowRunSchema, api=api)
    @responds(schema=JobMlflowRunSchema, api=api)
    def post(self, id: int, jobId: int):
        """Sets the mlflow run id for a Job"""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()),
            resource="ExperimentIdJobIdMlflowrunEndpoint",
            request_type="POST",
            experiment_id=id,
            job_id=jobId,
        )
        parsed_obj = request.parsed_obj  # type: ignore
        return self._experiment_job_id_mlflowrun_service.create(
            experiment_id=id,
            job_id=jobId,
            mlflow_run_id=parsed_obj["mlflow_run_id"],
            error_if_not_found=True,
            log=log,
        )


@api.route("/<int:id>/jobs/<int:jobId>/artifacts")
@api.param("id", "ID for the Experiment resource.")
@api.param("jobId", "ID for the Job resource.")
class ExperimentIdJobIdArtifactsEndpoint(Resource):
    @inject
    def __init__(
        self, job_artifact_service: JobArtifactService, *args, **kwargs
    ) -> None:
        """Initialize the jobs resource.

        All arguments are provided via dependency injection.

        Args:
            job_id_service: A JobIdStatusService object.
        """
        self._job_artifact_service = job_artifact_service
        super().__init__(*args, **kwargs)

    @login_required
    @accepts(
        schema=ArtifactSchema(exclude=["groupId", "jobId"]),
        model_name="JobArtifactSchema",
        api=api,
    )
    @responds(schema=ArtifactSchema, api=api)
    def post(self, id: int, jobId: int):
        """Creates an Artifact resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Artifact", request_type="POST"
        )
        log.debug("Request received")
        parsed_obj = request.parsed_obj  # type: ignore

        artifact = self._job_artifact_service.create(
            experiment_id=id,
            job_id=jobId,
            uri=parsed_obj["uri"],
            description=parsed_obj["description"],
            log=log,
        )
        return utils.build_artifact(artifact)


@api.route("/<int:id>/entrypoints")
@api.param("id", "ID for the Experiment resource.")
class ExperimentIdEntrypointsEndpoint(Resource):
    @inject
    def __init__(
        self,
        experiment_id_entrypoints_service: ExperimentIdEntrypointsService,
        *args,
        **kwargs,
    ) -> None:
        """Initialize the experiment resource.

        All arguments are provided via dependency injection.

        Args:
            experiment_id_entrypoints_service: An ExperimentIdEntrypointsService object.
        """
        self._experiment_id_entrypoints = experiment_id_entrypoints_service
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=EntrypointRefSchema(many=True), api=api)
    def get(self, id: int):
        """Gets the list of Entrypoints for the resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Experiment", request_type="GET"
        )
        entrypoints = self._experiment_id_entrypoints.get(id, log=log)
        return [utils.build_entrypoint_ref(entrypoint) for entrypoint in entrypoints]

    @login_required
    @accepts(schema=IdListSchema, api=api)
    @responds(schema=EntrypointRefSchema(many=True), api=api)
    def post(self, id: int):
        """Appends one or more Entrypoints to the resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Experiment", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # type: ignore
        entrypoints = cast(
            list[models.EntryPoint],
            self._experiment_id_entrypoints.append(
                id, entrypoint_ids=parsed_obj["ids"], error_if_not_found=True, log=log
            ),
        )
        return [utils.build_entrypoint_ref(entrypoint) for entrypoint in entrypoints]

    @login_required
    @accepts(schema=IdListSchema, api=api)
    @responds(schema=EntrypointRefSchema(many=True), api=api)
    def put(self, id: int):
        """Replaces one or more Entrypoints to the resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Experiment", request_type="POST"
        )
        parsed_obj = request.parsed_obj  # type: ignore
        entrypoints = self._experiment_id_entrypoints.modify(
            id, entrypoint_ids=parsed_obj["ids"], error_if_not_found=True, log=log
        )
        return [utils.build_entrypoint_ref(entrypoint) for entrypoint in entrypoints]

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int):
        """Removes all Entrypoints from the resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Experiment", request_type="DELETE"
        )
        return self._experiment_id_entrypoints.delete(
            id, error_if_not_found=True, log=log
        )


@api.route("/<int:id>/entrypoints/<int:entrypointId>")
@api.param("id", "ID for the Experiment resource.")
@api.param("entrypointId", "ID for the Entrypoint resource.")
class ExperimentIdEntrypointsId(Resource):
    @inject
    def __init__(
        self,
        experiments_id_entrypoints_id_service: ExperimentIdEntrypointsIdService,
        *args,
        **kwargs,
    ) -> None:
        self._experiments_id_entrypoints_id_service = (
            experiments_id_entrypoints_id_service
        )
        """Initialize the experiment resource.

        All arguments are provided via dependency injection.

        Args:
            experiment_id_entrypoints_id_service: An ExperimentIdEntrypointsIdService
            object.
        """
        super().__init__(*args, **kwargs)

    @login_required
    @responds(schema=IdStatusResponseSchema, api=api)
    def delete(self, id: int, entrypointId):
        """Removes a Entrypoint from the Experiment resource."""
        log = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="Experiment", request_type="GET"
        )
        return self._experiments_id_entrypoints_id_service.delete(
            id, entrypointId, log=log
        )


ExperimentDraftResource = generate_resource_drafts_endpoint(
    api,
    resource_name=RESOURCE_TYPE,
    route_prefix=V1_EXPERIMENTS_ROUTE,
    request_schema=ExperimentDraftSchema,
)
ExperimentDraftIdResource = generate_resource_drafts_id_endpoint(
    api,
    resource_name=RESOURCE_TYPE,
    request_schema=ExperimentDraftSchema(exclude=["groupId"]),
)
ExperimentIdDraftResource = generate_resource_id_draft_endpoint(
    api,
    resource_name=RESOURCE_TYPE,
    request_schema=ExperimentDraftSchema(exclude=["groupId"]),
)

ExperimentSnapshotsResource = generate_resource_snapshots_endpoint(
    api=api,
    resource_model=models.Experiment,
    resource_name=RESOURCE_TYPE,
    route_prefix=V1_EXPERIMENTS_ROUTE,
    searchable_fields=SEARCHABLE_FIELDS,
    page_schema=ExperimentPageSchema,
    build_fn=utils.build_experiment,
)
ExperimentSnapshotsIdResource = generate_resource_snapshots_id_endpoint(
    api=api,
    resource_model=models.Experiment,
    resource_name=RESOURCE_TYPE,
    response_schema=ExperimentSchema,
    build_fn=utils.build_experiment,
)

ExperimentTagsResource = generate_resource_tags_endpoint(
    api=api,
    resource_name=RESOURCE_TYPE,
)
ExperimentTagsIdResource = generate_resource_tags_id_endpoint(
    api=api, resource_name=RESOURCE_TYPE
)
