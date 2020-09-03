from typing import Any, Dict

from marshmallow import Schema, fields, post_load, pre_dump, validate

from mitre.securingai.restapi.shared.job_queue.model import JobQueue, JobStatus

from .interface import JobInterface, JobSubmitInterface
from .model import Job


class JobSchema(Schema):
    __model__ = Job

    jobId = fields.String(attribute="job_id")
    createdOn = fields.DateTime(attribute="created_on")
    lastModified = fields.DateTime(attribute="last_modified")
    queue = fields.String(validate=validate.OneOf(["tensorflow_cpu", "tensorflow_gpu"]))
    timeout = fields.String(attribute="timeout", allow_none=True)
    workflowUri = fields.String(attribute="workflow_uri")
    entryPoint = fields.String(attribute="entry_point")
    entryPointKwargs = fields.String(attribute="entry_point_kwargs", allow_none=True)
    dependsOn = fields.String(attribute="depends_on", allow_none=True)
    status = fields.String(
        validate=validate.OneOf(["queued", "started", "deferred", "finished", "failed"])
    )

    @post_load
    def deserialize_object(self, data: Dict[str, Any], many: bool, **kwargs) -> Job:
        def convert_enum_type(key: str, value: Any) -> Any:
            if key == "queue":
                return JobQueue[value]

            if key == "status":
                return JobStatus[value]

            return value

        job_interface: JobInterface = {
            k: convert_enum_type(k, v) for k, v in data.items()
        }
        return self.__model__(**job_interface)

    @pre_dump
    def serialize_object(self, data: Job, many: bool, **kwargs) -> JobInterface:
        return {
            "job_id": data.job_id,
            "created_on": data.created_on,
            "last_modified": data.last_modified,
            "queue": data.queue.name,
            "timeout": data.timeout,
            "workflow_uri": data.workflow_uri,
            "entry_point": data.entry_point,
            "entry_point_kwargs": data.entry_point_kwargs,
            "depends_on": data.depends_on,
            "status": data.status.name,
        }


class JobSubmitSchema(Schema):
    __model__ = Job

    queue = fields.String(validate=validate.OneOf(["tensorflow_cpu", "tensorflow_gpu"]))
    timeout = fields.String(attribute="timeout", allow_none=True)
    workflowUri = fields.String(attribute="workflow_uri")
    entryPoint = fields.String(attribute="entry_point")
    entryPointKwargs = fields.String(attribute="entry_point_kwargs", allow_none=True)
    dependsOn = fields.String(attribute="depends_on", allow_none=True)

    @post_load
    def deserialize_enums(self, data: Dict[str, Any], many: bool, **kwargs) -> Job:
        def convert_enum_type(key: str, value: Any) -> Any:
            if key == "queue":
                return JobQueue[value]

            return value

        job_submit_interface: JobSubmitInterface = {
            k: convert_enum_type(k, v) for k, v in data.items()
        }
        return self.__model__(**job_submit_interface)

    @pre_dump
    def serialize_object(self, data: Job, many: bool, **kwargs) -> JobSubmitInterface:
        return {
            "queue": data.queue.name,
            "timeout": data.timeout,
            "workflow_uri": data.workflow_uri,
            "entry_point": data.entry_point,
            "entry_point_kwargs": data.entry_point_kwargs,
            "depends_on": data.depends_on,
        }


