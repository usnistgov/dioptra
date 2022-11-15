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
from __future__ import annotations

from typing import Optional

import structlog
from injector import inject
from mlflow.exceptions import RestException
from mlflow.tracking import MlflowClient
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class MLFlowTrackingService(object):
    @inject
    def __init__(self, client: MlflowClient) -> None:
        self._client = client

    def create_experiment(self, experiment_name: str, **kwargs) -> Optional[str]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        try:
            experiment_id: str = self._client.create_experiment(name=experiment_name)
            return experiment_id

        except RestException as e:
            if e.error_code == "RESOURCE_ALREADY_EXISTS":
                log.warning(
                    "MLFlow experiment already exists", experiment_name=experiment_name
                )
                return None

            raise e

    def delete_experiment(self, experiment_id: int, **kwargs) -> Optional[bool]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        try:
            self._client.delete_experiment(experiment_id=experiment_id)

        except RestException as e:
            if e.error_code == "RESOURCE_DOES_NOT_EXIST":
                log.warning(
                    "MLFlow experiment does not exist", experiment_id=experiment_id
                )
                return None

            raise e

        return True

    def rename_experiment(
        self, experiment_id: int, new_name: str, **kwargs
    ) -> Optional[bool]:
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        try:
            self._client.rename_experiment(
                experiment_id=experiment_id, new_name=new_name
            )

        except RestException as e:
            if e.error_code == "RESOURCE_DOES_NOT_EXIST":
                log.warning(
                    "MLFlow experiment does not exist",
                    experiment_id=experiment_id,
                    new_name=new_name,
                )
                return None

            raise e

        return True
