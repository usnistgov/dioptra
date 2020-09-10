from typing import Any, Dict

from marshmallow import Schema, fields, post_dump, post_load, pre_dump, validate
from werkzeug.datastructures import FileStorage

from mitre.securingai.restapi.shared.job_queue.model import JobQueue, JobStatus

from .interface import JobInterface
from .model import Job, JobForm, JobFormData


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
    def stringify_enum_type(self, data: Job, many: bool, **kwargs) -> Job:
        if isinstance(data.queue, JobQueue):
            data.queue = data.queue.name

        if isinstance(data.status, JobStatus):
            data.status = data.status.name

        return data


class JobFormSchema(Schema):
    __model__ = JobFormData

    queue = fields.String(validate=validate.OneOf(["tensorflow_cpu", "tensorflow_gpu"]))
    timeout = fields.String(allow_none=True)
    entry_point = fields.String()
    entry_point_kwargs = fields.String(allow_none=True)
    depends_on = fields.String(allow_none=True)
    workflow = fields.Raw()

    @pre_dump
    def serialize_object(self, data: JobForm, many: bool, **kwargs) -> Dict[str, Any]:
        return {
            "queue": data.queue.data,
            "timeout": data.timeout.data or None,
            "entry_point": data.entry_point.data,
            "entry_point_kwargs": data.entry_point_kwargs.data or None,
            "depends_on": data.depends_on.data or None,
            "workflow": data.workflow.data,
        }

    @post_dump
    def convert_enum_types(
        self, data: Dict[str, Any], many: bool, **kwargs
    ) -> JobFormData:
        def convert_enum_type(key: str, value: Any) -> Any:
            if key == "queue":
                return JobQueue[value]

            return value

        return self.__model__({k: convert_enum_type(k, v) for k, v in data.items()})


job_submit_form_schema = [
    dict(name="queue", type=JobQueue, location="form"),
    dict(name="timeout", type=str, location="form"),
    dict(name="entry_point", type=str, location="form"),
    dict(name="entry_point_kwargs", type=str, location="form"),
    dict(name="depends_on", type=str, location="form"),
    dict(name="workflow", type=FileStorage, location="files"),
]
