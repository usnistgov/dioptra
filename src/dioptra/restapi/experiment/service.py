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
"""The server-side functions that perform experiment endpoint operations."""
from __future__ import annotations

import datetime
from typing import Any, cast

import structlog
from injector import inject
from mlflow.exceptions import RestException
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db
from dioptra.restapi.shared.mlflow_tracking.service import MLFlowTrackingService
from dioptra.restapi.utils import slugify

from .errors import (
    ExperimentAlreadyExistsError,
    ExperimentDoesNotExistError,
    ExperimentMLFlowTrackingAlreadyExistsError,
    ExperimentMLFlowTrackingDoesNotExistError,
    ExperimentMLFlowTrackingRegistrationError,
)
from .model import Experiment

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class ExperimentService(object):
    @inject
    def __init__(
        self,
        mlflow_tracking_service: MLFlowTrackingService,
        experiment_name_service: ExperimentNameService,
    ) -> None:
        """Initialize the experiment service.

        All arguments are provided via dependency injection.

        Args:
            mlflow_tracking_service: The MLflow tracking service.
            experiment_name_service: The experiment name service.
        """
        self._mlflow_tracking_service = mlflow_tracking_service
        self._experiment_name_service = experiment_name_service

    def create(
        self,
        experiment_name: str,
        **kwargs,
    ) -> Experiment:
        """Create a new experiment.

        Args:
            experiment_name: The name of the experiment.

        Returns:
            The newly created experiment object.

        Raises:
            ExperimentAlreadyExistsError: If an experiment with the given name already
                exists.
            ExperimentMLFlowTrackingAlreadyExistsError: If an MLflow experiment with
                the same name already exists.
            ExperimentMLFlowTrackingRegistrationError: If there is an error registering
                the experiment with MLflow.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        experiment_name = slugify(experiment_name)

        if self._experiment_name_service.get(experiment_name, log=log) is not None:
            raise ExperimentAlreadyExistsError

        timestamp = datetime.datetime.now()

        try:
            experiment_id = self._mlflow_tracking_service.create_experiment(
                experiment_name
            )

        except RestException as exc:
            raise ExperimentMLFlowTrackingRegistrationError from exc

        if experiment_id is None:
            raise ExperimentMLFlowTrackingAlreadyExistsError

        new_experiment = Experiment(
            experiment_id=int(experiment_id),
            name=experiment_name,
            created_on=timestamp,
            last_modified=timestamp,
        )
        db.session.add(new_experiment)
        db.session.commit()
        log.info(
            "Experiment registration successful",
            experiment_id=new_experiment.experiment_id,
        )
        return new_experiment

    def delete(self, experiment_id: int, **kwargs) -> dict[str, Any]:
        """Delete an experiment.

        Args:
            experiment_id: The unique identifier of the experiment.

        Returns:
            A dictionary reporting the status of the request.

        Raises:
            ExperimentMLFlowTrackingDoesNotExistError: If the experiment does not exist
                in MLflow.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841
        experiment = self.get(experiment_id=experiment_id)

        if experiment is None:
            return {"status": "Success", "id": []}

        response = self._mlflow_tracking_service.delete_experiment(
            experiment_id=experiment_id
        )

        if response is None:
            raise ExperimentMLFlowTrackingDoesNotExistError

        experiment.update(changes={"is_deleted": True})
        db.session.commit()
        return {"status": "Success", "id": [experiment_id]}

    def rename(self, experiment_id: int, new_name: str, **kwargs) -> Experiment:
        """Rename an experiment.

        Args:
            experiment_id: The unique identifier of the experiment.
            new_name: The new name for the experiment.

        Returns:
            The updated experiment object.

        Raises:
            ExperimentMLFlowTrackingDoesNotExistError: If the experiment does not exist
                in MLflow.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841
        new_name = slugify(new_name)
        experiment = cast(
            Experiment, self.get(experiment_id, error_if_not_found=True, log=log)
        )
        response = self._mlflow_tracking_service.rename_experiment(
            experiment_id=experiment_id, new_name=new_name, log=log
        )

        if response is None:
            raise ExperimentMLFlowTrackingDoesNotExistError

        experiment.update(changes={"name": new_name})
        db.session.commit()
        log.info("Experiment renamed", queue_id=experiment_id, new_name=new_name)
        return experiment

    def get_all(self, **kwargs) -> list[Experiment]:
        """Fetch the list of all experiments.

        Returns:
            A list of experiment objects.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841
        return Experiment.query.filter_by(is_deleted=False).all()  # type: ignore

    def get(
        self, experiment_id: int, error_if_not_found: bool = False, **kwargs
    ) -> Experiment | None:
        """Fetch an experiment by its unique identifier.

        Args:
            experiment_id: The unique identifier of the experiment.
            error_if_not_found: If True, raise an error if the experiment is not found.
                Defaults to False.

        Returns:
            The experiment object if found, otherwise None.

        Raises:
            ExperimentDoesNotExistError: If the experiment is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())  # noqa: F841
        experiment = Experiment.query.filter_by(
            experiment_id=experiment_id, is_deleted=False
        ).first()

        if experiment is None:
            if error_if_not_found:
                log.error("Experiment not found", experiment_id=experiment_id)
                raise ExperimentDoesNotExistError

            return None

        return cast(Experiment, experiment)


class ExperimentNameService(object):
    @inject
    def __init__(
        self,
        mlflow_tracking_service: MLFlowTrackingService,
    ) -> None:
        """Initialize the experiment name service.

        All arguments are provided via dependency injection.

        Args:
            mlflow_tracking_service: The MLflow tracking service.
        """
        self._mlflow_tracking_service = mlflow_tracking_service

    def get(
        self,
        experiment_name: str,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> Experiment | None:
        """Fetch an experiment by its name.

        Args:
            experiment_name: The name of the experiment.
            error_if_not_found: If True, raise an error if the experiment is not found.
                Defaults to False.

        Returns:
            The experiment object if found, otherwise None.

        Raises:
            ExperimentDoesNotExistError: If the experiment is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        experiment_name = slugify(experiment_name)
        log.info("Get experiment by name", experiment_name=experiment_name)
        experiment = Experiment.query.filter_by(
            name=experiment_name, is_deleted=False
        ).first()

        if experiment is None:
            if error_if_not_found:
                log.error("Experiment not found", experiment_name=experiment_name)
                raise ExperimentDoesNotExistError

            return None

        return cast(Experiment, experiment)

    def delete(self, experiment_name: str, **kwargs) -> dict[str, Any]:
        """Delete an experiment by name.

        Args:
            experiment_name: The name of the experiment.

        Returns:
            A dictionary reporting the status of the request.

        Raises:
            ExperimentMLFlowTrackingDoesNotExistError: If the experiment does not exist
                in MLflow.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.info("Delete experiment by name", experiment_name=experiment_name)

        if (experiment := self.get(experiment_name, log=log)) is None:
            return {"status": "Success", "name": []}

        response: bool | None = self._mlflow_tracking_service.delete_experiment(
            experiment_id=experiment.experiment_id
        )

        if response is None:
            raise ExperimentMLFlowTrackingDoesNotExistError

        experiment.update(changes={"is_deleted": True})
        db.session.commit()
        log.info("Experiment deleted", experiment_name=experiment_name)
        return {"status": "Success", "name": [experiment_name]}
