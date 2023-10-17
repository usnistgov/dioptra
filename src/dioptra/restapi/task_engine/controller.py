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
import flask
from flask_accepts import accepts, responds
from flask_restx import Namespace, Resource
from injector import inject

from dioptra.restapi.job.model import Job
from dioptra.restapi.job.schema import JobSchema
from dioptra.restapi.job.service import JobService

from .schema import TaskEngineSubmission

api: Namespace = Namespace(
    "TaskEngine",
    description="Run experiments via the task engine",
)


@api.route("/")
class TaskEngineResource(Resource):
    @inject
    def __init__(self, job_service: JobService, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._job_service = job_service

    @accepts(schema=TaskEngineSubmission, api=api)
    @responds(schema=JobSchema, api=api)
    def post(self) -> Job:
        post_obj = flask.request.parsed_obj  # type: ignore

        new_job = self._job_service.submit_task_engine(
            queue_name=post_obj["queue"],
            experiment_name=post_obj["experimentName"],
            experiment_description=post_obj["experimentDescription"],
            global_parameters=post_obj.get("globalParameters"),
            timeout=post_obj.get("timeout"),
            depends_on=post_obj.get("dependsOn"),
        )

        return new_job
