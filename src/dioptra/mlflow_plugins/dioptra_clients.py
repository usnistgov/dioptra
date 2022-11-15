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
import datetime
import os
from typing import Any, Dict, Optional

import structlog
from flask import Flask
from sqlalchemy.exc import IntegrityError
from structlog.stdlib import BoundLogger

from dioptra.restapi import create_app
from dioptra.restapi.app import db
from dioptra.restapi.models import Experiment, Job

ENVVAR_RESTAPI_ENV = "DIOPTRA_RESTAPI_ENV"
ENVVAR_JOB_ID = "DIOPTRA_RQ_JOB_ID"

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class DioptraDatabaseClient(object):
    @property
    def app(self) -> Flask:
        app: Flask = create_app(env=self.restapi_env)
        return app

    @property
    def job_id(self) -> Optional[str]:
        return os.getenv(ENVVAR_JOB_ID)

    @property
    def restapi_env(self) -> Optional[str]:
        return os.getenv(ENVVAR_RESTAPI_ENV)

    def get_active_job(self) -> Optional[Dict[str, Any]]:
        if self.job_id is None:
            return None

        with self.app.app_context():
            job: Job = Job.query.get(self.job_id)
            return {
                "job_id": job.job_id,
                "queue": job.queue.name,
                "depends_on": job.depends_on,
                "timeout": job.timeout,
            }

    def update_active_job_status(self, status: str) -> None:
        if self.job_id is None:
            return None

        self.update_job_status(job_id=self.job_id, status=status)

    def update_job_status(self, job_id: str, status: str) -> None:
        LOGGER.info(
            f"=== Updating job status for job with ID '{self.job_id}' to "
            f"{status} ==="
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

        LOGGER.info("=== Setting MLFlow run ID in the Dioptra database ===")

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
            f"=== Restoring MLFlow job id '{job_id}' in the Dioptra " "database ==="
        )

        with self.app.app_context():
            job: Job = Job.query.get(job_id)  # noqa: F841

            try:
                db.session.commit()

            except IntegrityError:
                db.session.rollback()
                raise

    def delete_job(self, job_id: str) -> None:
        LOGGER.info(
            f"=== Deleting MLFlow job id '{job_id}' from the Dioptra " "database ==="
        )

        with self.app.app_context():
            job: Job = Job.query.get(job_id)  # noqa: F841

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
            f"'{experiment_id}' in Dioptra database ==="
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
            f"=== Renaming MLFlow experiment id '{experiment_id}' to '{new_name}' in "
            "the Dioptra database ==="
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
            f"=== Deleting MLFlow experiment id '{experiment_id}' from the Dioptra "
            "database ==="
        )

        with self.app.app_context():
            experiment: Experiment = Experiment.query.get(experiment_id)  # noqa: F841

            try:
                db.session.commit()

            except IntegrityError:
                db.session.rollback()
                raise
