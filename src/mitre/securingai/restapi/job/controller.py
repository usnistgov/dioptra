import uuid

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from injector import inject
from structlog import BoundLogger
from structlog._config import BoundLoggerLazyProxy

from .model import Job
from .schema import JobSchema, JobSubmitSchema
from .service import JobService

LOGGER: BoundLoggerLazyProxy = structlog.get_logger()

api: Namespace = Namespace(
    "Job", description="Endpoint for the job queue.",
)


@api.route("/")
class JobResource(Resource):
    @inject
    def __init__(self, *args, job_service: JobService, **kwargs) -> None:
        self._job_service = job_service
        super().__init__(*args, **kwargs)

    @accepts(schema=JobSubmitSchema, api=api)
    @responds(schema=JobSchema, api=api)
    def post(self) -> Job:
        log: BoundLogger = LOGGER.new(request_id=str(uuid.uuid4()))  # noqa: F841

        return self._job_service.submit(request.parsed_obj)


@api.route("/<string:jobId>")
@api.param("jobId", "Unique job identifier")
class JobIdResource(Resource):
    @inject
    def __init__(self, *args, job_service: JobService, **kwargs) -> None:
        self._job_service = job_service
        super().__init__(*args, **kwargs)

    @responds(schema=JobSchema, api=api)
    def get(self, jobId: str) -> Job:
        return self._job_service.get_by_id(jobId)
