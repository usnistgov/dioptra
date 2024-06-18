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

from typing import Any, Final, cast

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import func, select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import BackendDatabaseError, SearchNotImplementedError
from dioptra.restapi.v1.groups.service import GroupIdService

from .errors import ExperimentAlreadyExistsError, ExperimentDoesNotExistError

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "experiment"


class ExperimentService(object):
    """The service methods for registering and managing experiments by their unique
    id."""

    @inject
    def __init__(
        self,
        experiment_name_service: ExperimentNameService,
        group_id_service: GroupIdService,
    ) -> None:
        """Initialize the experiment service.

        All arguments are provided via dependency injection.

        Args:
            experiment_name_service: An ExperimentNameService object.
            group_id_service: A GroupIdService object.
        """
        self._experiment_name_service = experiment_name_service
        self._group_id_service = group_id_service

    def create(
        self,
        name: str,
        description: str,
        entrypoint_ids: list[int],
        tag_ids: list[int],
        group_id: int,
        commit: bool = True,
        **kwargs,
    ) -> models.Experiment:
        """Create a new experiment.

        Args:
            name: The name of the experiment. The combination of experiment and group_id
                must be unique.
            description: The description of the experiment.
            entrypoint_ids: The list of entrypoint_ids to associate with the experiment.
            tag_ids: The list of tag_ids to associate with the experiment.
            group_id: The group that will own the experiment.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created experiment object.

        Raises:
            ExperimentAlreadyExistsError: If an experiment with the given name already
                exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        # TODO: add association with entrypoints
        # TODO: apply tags

        if (
            self._experiment_name_service.get(name, group_id=group_id, log=log)
            is not None
        ):
            log.debug("Experiment name already exists", name=name, group_id=group_id)
            raise ExperimentAlreadyExistsError

        group = self._group_id_service.get(group_id, error_if_not_found=True)

        resource = models.Resource(resource_type="experiment", owner=group)
        new_experiment = models.Experiment(
            name=name,
            description=description,
            resource=resource,
            creator=current_user,
        )
        db.session.add(new_experiment)

        if commit:
            db.session.commit()
            log.debug(
                "Experiment registration successful",
                experiment_id=new_experiment.resource_id,
                name=new_experiment.name,
            )

        return new_experiment

    def get(
        self,
        group_id: int | None,
        search_string: str,
        page_index: int,
        page_length: int,
        **kwargs,
    ) -> tuple[list[models.Experiment], int]:
        """Fetch a list of experiments, optionally filtering by search string and paging
        parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first page to be returned.
            page_length: The maximum number of experiments to be returned.

        Returns:
            A tuple containing a list of experiments and the total number of experiments
            matching the query.

        Raises:
            SearchNotImplementedError: If a search string is provided.
            BackEndDatabaseError: If the database query returns a None when counting
                the number of experiments.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of experiments")

        filters = list()

        if group_id is not None:
            filters.append(models.Resource.group_id == group_id)

        if search_string:
            log.debug("Searching is not implemented", search_string=search_string)
            raise SearchNotImplementedError

        experiments_count_stmt = (
            select(func.count(models.Experiment.resource_id))
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Experiment.resource_snapshot_id,
            )
        )
        total_num_experiments = db.session.scalars(experiments_count_stmt).first()

        if total_num_experiments is None:
            log.error(
                "The database query returned a None when counting the number of "
                "experiments when it should return a number.",
                sql=str(experiments_count_stmt),
            )
            raise BackendDatabaseError

        if total_num_experiments == 0:
            return cast(list[models.Experiment], []), total_num_experiments

        experiments_stmt = (
            select(models.Experiment)
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Experiment.resource_snapshot_id,
            )
            .offset(page_index)
            .limit(page_length)
        )
        experiments = list(db.session.scalars(experiments_stmt).all())

        return experiments, total_num_experiments


class ExperimentIdService(object):
    """The service methods for registering and managing experiments by their unique
    id.
    """

    @inject
    def __init__(
        self,
        experiment_name_service: ExperimentNameService,
    ) -> None:
        """Initialize the experiment service.

        All arguments are provided via dependency injection.

        Args:
            experiment_name_service: An ExperimentNameService object.
        """
        self._experiment_name_service = experiment_name_service

    def get(
        self,
        experiment_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> models.Experiment | None:
        """Fetch an experiment by its unique id.

        Args:
            experiment_id: The unique id of the experiment.
            error_if_not_found: If True, raise an error if the experiment is not found.
                Defaults to False.

        Returns:
            The experiment object if found, otherwise none.

        Raises:
            ExperimentDoesNotExistError: If the experiment is not found and if
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get experiment by id", experiment_id=experiment_id)

        stmt = (
            select(models.Experiment)
            .join(models.Resource)
            .where(
                models.Experiment.resource_id == experiment_id,
                models.Experiment.resource_snapshot_id
                == models.Resource.latest_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        experiment = db.session.scalars(stmt).first()

        if experiment is None:
            if error_if_not_found:
                log.debug("Experiment not found", experiment_id=experiment_id)
                raise ExperimentDoesNotExistError

            return None

        return experiment

    def modify(
        self,
        experiment_id: int,
        name: str,
        description: str,
        entrypoint_ids: list[int],
        commit: bool = True,
        **kwargs,
    ) -> models.Experiment | None:
        """Modify an experiment.

        Args:
            experiment_id: The unique if of the experiment.
            name: The new name of the experiment.
            description: The new description of the experiment.
            entrypoint_ids: The new list of entrypoints to associate with the
                experiment.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated experiment object.

        Raises:
            ExperimentDoesNotExistError: If the experiment is not found and
                `error_if_not_found` is True.
            ExperimentAlreadyExistsError: If the experiment name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        # TODO: add association with entrypoints

        experiment = cast(
            models.Experiment, self.get(experiment_id, error_if_not_found=True, log=log)
        )
        group_id = experiment.resource.group_id

        if (
            name != experiment.name
            and self._experiment_name_service.get(name, group_id=group_id, log=log)
            is not None
        ):
            log.debug("Experiment name already exists", name=name, group_id=group_id)
            raise ExperimentAlreadyExistsError

        new_experiment = models.Experiment(
            name=name,
            description=description,
            resource=experiment.resource,
            creator=current_user,
        )
        db.session.add(new_experiment)

        if commit:
            db.session.commit()
            log.debug(
                "Experiment modification successful",
                experiment_id=experiment_id,
                name=name,
            )

        return new_experiment

    def delete(self, experiment_id: int, **kwargs) -> dict[str, Any]:
        """Delete an experiment.

        Args:
            experiment_id: The unique id of the experiment.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        stmt = select(models.Resource).filter_by(
            resource_id=experiment_id, resource_type=RESOURCE_TYPE, is_deleted=False
        )
        experiment_resource = db.session.scalar(stmt)

        if experiment_resource is None:
            raise ExperimentDoesNotExistError

        deleted_resource_lock = models.ResourceLock(
            resource_lock_type="delete",
            resource=experiment_resource,
        )
        db.session.add(deleted_resource_lock)
        db.session.commit()
        log.debug("Experiment deleted", experiment_id=experiment_id)

        return {"status": "Success", "id": [experiment_id]}


class ExperimentNameService(object):
    """The service methods for managing experiments by their name."""

    def get(
        self,
        name: str,
        group_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> models.Experiment | None:
        """Fetch an experiment by its name.

        Args:
            name: The name of the experiment.
            group_id: The group id of the experiment.
            error_if_not_found: If True, raise an error if the experiment is not found.
                Defaults to False.

        Returns:
            The experiment object if found, otherwise None.

        Raises:
            ExperimentDoesNotExistError: If the experiment is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get experiment by name", experiment_name=name, group_id=group_id)

        stmt = (
            select(models.Experiment)
            .join(models.Resource)
            .where(
                models.Experiment.name == name,
                models.Resource.group_id == group_id,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Experiment.resource_snapshot_id,
            )
        )
        experiment = db.session.scalars(stmt).first()

        if experiment is None:
            if error_if_not_found:
                log.debug("Experiment not found", name=name)
                raise ExperimentDoesNotExistError

            return None

        return experiment
