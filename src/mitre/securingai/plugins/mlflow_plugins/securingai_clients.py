import datetime
import os
import uuid
from typing import Optional

import structlog
from flask import Flask
from sqlalchemy.exc import IntegrityError

from mitre.securingai.restapi import create_app
from mitre.securingai.restapi.app import db
from mitre.securingai.restapi.models import Experiment, Job
from mitre.securingai.restapi.shared.job_queue.model import JobStatus


ENVVAR_RESTAPI_ENV = "AI_RESTAPI_ENV"
ENVVAR_JOB_ID = "AI_RQ_JOB_ID"

LOGGER = structlog.get_logger()


class SecuringAIDatabaseClient(object):
    @property
    def app(self) -> Flask:
        return create_app(env=self.restapi_env)

    @property
    def job_id(self) -> Optional[str]:
        return os.getenv(ENVVAR_JOB_ID)

    @property
    def restapi_env(self) -> Optional[str]:
        return os.getenv(ENVVAR_RESTAPI_ENV)

    def get_active_job(self) -> Optional[Job]:
        if self.job_id is None:
            return None

        with self.app.app_context():
            return Job.query.get(self.job_id)

    def update_active_job_status(self, status: JobStatus) -> None:
        if self.job_id is None:
            return None

        self.update_job_status(job_id=self.job_id, status=status)

    def update_job_status(self, job_id: str, status: JobStatus) -> None:
        LOGGER.info(
            f"=== Updating job status for job with ID '{self.job_id}' to "
            f"{status.name} ==="
        )

        with self.app.app_context():
            job = Job.query.get(job_id)

            if job.status != status:
                job.update(changes={"status": status})

                try:
                    db.session.commit()

                except IntegrityError:
                    db.session.rollback()
                    raise

    def set_mlflow_run_id_in_db(self, run_id: str) -> None:
        if self.job_id is None:
            return None

        LOGGER.info("=== Setting MLFlow run ID in Securing AI database ===")

        with self.app.app_context():
            job = Job.query.get(self.job_id)
            job.update(changes={"mlflow_run_id": run_id})

            try:
                db.session.commit()

            except IntegrityError:
                db.session.rollback()
                raise

    def create_job(self, job_id: str, experiment_id: int) -> None:
        timestamp = datetime.datetime.now()

        with self.app.app_context():
            new_job: Job = Job(
                job_id=job_id,
                experiment_id=experiment_id,
                created_on=timestamp,
                last_modified=timestamp,
            )
            db.session.add(new_job)

            try:
                db.session.commit()

            except IntegrityError:
                db.session.rollback()
                raise

    def restore_job(self, job_id: str) -> None:
        LOGGER.info(
            f"=== Restoring MLFlow job id '{job_id}' in the Securing AI " "database ==="
        )

        with self.app.app_context():
            job: Job = Job.query.get(job_id)

            try:
                db.session.commit()

            except IntegrityError:
                db.session.rollback()
                raise

    def delete_job(self, job_id: str) -> None:
        LOGGER.info(
            f"=== Deleting MLFlow job id '{job_id}' from the Securing AI "
            "database ==="
        )

        with self.app.app_context():
            job: Job = Job.query.get(job_id)

            try:
                db.session.commit()

            except IntegrityError:
                db.session.rollback()
                raise

    def get_experiment_by_id(self, experiment_id: int) -> Optional[Experiment]:
        return Experiment.query.get(experiment_id)

    def create_experiment(self, experiment_name: str, experiment_id: int) -> None:
        timestamp = datetime.datetime.now()

        LOGGER.info(
            f"=== Registering MLFlow experiment '{experiment_name}' with id "
            f"'{experiment_id}' in Securing AI database ==="
        )

        with self.app.app_context():
            new_experiment: Experiment = Experiment(
                experiment_id=experiment_id,
                name=experiment_name,
                created_on=timestamp,
                last_modified=timestamp,
            )
            db.session.add(new_experiment)

            try:
                db.session.commit()

            except IntegrityError:
                db.session.rollback()
                raise

    def rename_experiment(self, experiment_id: int, new_name: str) -> None:
        LOGGER.info(
            f"=== Renaming MLFlow experiment id '{experiment_id}' to '{new_name}' in the"
            " Securing AI database ==="
        )

        with self.app.app_context():
            experiment: Experiment = Experiment.query.get(experiment_id)
            experiment.update(changes={"name": new_name})

            try:
                db.session.commit()

            except IntegrityError:
                db.session.rollback()
                raise

    def delete_experiment(self, experiment_id: int) -> None:
        LOGGER.info(
            f"=== Deleting MLFlow experiment id '{experiment_id}' from the Securing AI "
            "database ==="
        )

        with self.app.app_context():
            experiment: Experiment = Experiment.query.get(experiment_id)

            try:
                db.session.commit()

            except IntegrityError:
                db.session.rollback()
                raise
