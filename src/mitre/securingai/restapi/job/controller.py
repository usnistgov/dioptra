import uuid
from typing import List

import structlog
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from injector import inject
from structlog import BoundLogger
from structlog._config import BoundLoggerLazyProxy

from mitre.securingai.restapi.shared.job_queue.model import JobStatus

from .model import Job, JobForm, JobFormData
from .schema import JobSchema, JobFormSchema, job_submit_form_schema
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

    @responds(schema=JobSchema(many=True), api=api)
    def get(self) -> List[Job]:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="job", request_type="GET"
        )  # noqa: F841
        log.info("Request received")
        return self._job_service.get_all(log=log)

    @accepts(job_submit_form_schema, api=api)
    @responds(schema=JobSchema, api=api)
    def post(self) -> Job:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="job", request_type="POST"
        )  # noqa: F841
        schema: JobFormSchema = JobFormSchema()
        job_form: JobForm = JobForm()

        log.info("Request received")

        if job_form.validate_on_submit():
            log.info("Form validation successful")
            return self._job_service.submit(
                job_form_data=schema.dump(job_form), log=log
            )

        log.warning("Form validation failed")
        return Job(status=JobStatus.failed)


@api.route("/<string:jobId>")
@api.param("jobId", "Unique job identifier")
class JobIdResource(Resource):
    @inject
    def __init__(self, *args, job_service: JobService, **kwargs) -> None:
        self._job_service = job_service
        super().__init__(*args, **kwargs)

    @responds(schema=JobSchema, api=api)
    def get(self, jobId: str) -> Job:
        log: BoundLogger = LOGGER.new(
            request_id=str(uuid.uuid4()), resource="jobId", request_type="GET"
        )  # noqa: F841
        log.info("Request received", job_id=jobId)
        return self._job_service.get_by_id(jobId, log=log)
