from typing import Any, Dict

from marshmallow import Schema, fields, post_dump, post_load, pre_dump, validate
from werkzeug.datastructures import FileStorage

from .model import Job, JobForm, JobFormData


class JobSchema(Schema):
    __model__ = Job

    jobId = fields.String(attribute="job_id")
    mlflowRunId = fields.String(attribute="mlflow_run_id", allow_none=True)
    experimentId = fields.Integer(attribute="experiment_id")
    queueId = fields.Integer(attribute="queue_id")
    createdOn = fields.DateTime(attribute="created_on")
    lastModified = fields.DateTime(attribute="last_modified")
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
        return self.__model__(**data)


class JobFormSchema(Schema):
    __model__ = JobFormData

    experiment_name = fields.String(required=True)
    queue = fields.String(required=True)
    timeout = fields.String(allow_none=True)
    entry_point = fields.String(required=True)
    entry_point_kwargs = fields.String(allow_none=True)
    depends_on = fields.String(allow_none=True)
    workflow = fields.Raw()

    @pre_dump
    def extract_data_from_form(
        self, data: JobForm, many: bool, **kwargs
    ) -> Dict[str, Any]:
        def slugify(text: str) -> str:
            return text.lower().strip().replace(" ", "-")

        return {
            "experiment_name": slugify(data.experiment_name.data),
            "queue": slugify(data.queue.data),
            "timeout": data.timeout.data or None,
            "entry_point": data.entry_point.data,
            "entry_point_kwargs": data.entry_point_kwargs.data or None,
            "depends_on": data.depends_on.data or None,
            "workflow": data.workflow.data,
        }

    @post_dump
    def serialize_object(
        self, data: Dict[str, Any], many: bool, **kwargs
    ) -> JobFormData:
        return self.__model__(**data)


job_submit_form_schema = [
    dict(name="experiment_name", type=str, location="form"),
    dict(name="queue", type=str, location="form"),
    dict(name="timeout", type=str, location="form"),
    dict(name="entry_point", type=str, location="form"),
    dict(name="entry_point_kwargs", type=str, location="form"),
    dict(name="depends_on", type=str, location="form"),
    dict(name="workflow", type=FileStorage, location="files"),
]
