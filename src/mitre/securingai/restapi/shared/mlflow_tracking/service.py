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
