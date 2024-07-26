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
from sqlalchemy import Integer, func, select
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.db.models.constants import resource_lock_types
from dioptra.restapi.errors import BackendDatabaseError
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.entrypoints.errors import EntrypointDoesNotExistError
from dioptra.restapi.v1.entrypoints.service import EntrypointIdsService
from dioptra.restapi.v1.groups.service import GroupIdService
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters

from .errors import ExperimentAlreadyExistsError, ExperimentDoesNotExistError

LOGGER: BoundLogger = structlog.stdlib.get_logger()

RESOURCE_TYPE: Final[str] = "experiment"
SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "name": lambda x: models.Experiment.name.like(x, escape="/"),
    "description": lambda x: models.Experiment.description.like(x, escape="/"),
    "tag": lambda x: models.Experiment.tags.any(models.Tag.name.like(x, escape="/")),
}


class ExperimentService(object):
    """The service methods for registering and managing experiments by their unique
    id."""

    @inject
    def __init__(
        self,
        entrypoint_ids_service: EntrypointIdsService,
        experiment_name_service: ExperimentNameService,
        group_id_service: GroupIdService,
    ) -> None:
        """Initialize the experiment service.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_ids_service: An EntrypointIdsService object.
            experiment_name_service: An ExperimentNameService object.
            group_id_service: A GroupIdService object.
        """
        self._entrypoint_ids_service = entrypoint_ids_service
        self._experiment_name_service = experiment_name_service
        self._group_id_service = group_id_service

    def create(
        self,
        name: str,
        description: str,
        group_id: int,
        entrypoint_ids: list[int] | None = None,
        commit: bool = True,
        **kwargs,
    ) -> utils.ExperimentDict:
        """Create a new experiment.

        Args:
            name: The name of the experiment. The combination of experiment and group_id
                must be unique.
            description: The description of the experiment.
            group_id: The group that will own the experiment.
            entrypoints_ids: The list of entrypoints for the experiment.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created experiment object.

        Raises:
            ExperimentAlreadyExistsError: If an experiment with the given name already
                exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if (
            self._experiment_name_service.get(name, group_id=group_id, log=log)
            is not None
        ):
            log.debug("Experiment name already exists", name=name, group_id=group_id)
            raise ExperimentAlreadyExistsError

        group = self._group_id_service.get(group_id, error_if_not_found=True)
        entrypoints = (
            self._entrypoint_ids_service.get(
                entrypoint_ids, error_if_not_found=True, log=log
            )
            if entrypoint_ids is not None
            else []
        )

        resource = models.Resource(resource_type="experiment", owner=group)
        new_experiment = models.Experiment(
            name=name,
            description=description,
            resource=resource,
            creator=current_user,
        )
        new_experiment.children.extend(
            entrypoint.resource for entrypoint in entrypoints
        )
        db.session.add(new_experiment)

        if commit:
            db.session.commit()
            log.debug(
                "Experiment registration successful",
                experiment_id=new_experiment.resource_id,
                name=new_experiment.name,
            )

        return utils.ExperimentDict(
            experiment=new_experiment,
            entrypoints=entrypoints,
            queue=None,
            has_draft=False,
        )

    def get(
        self,
        group_id: int | None,
        search_string: str,
        page_index: int,
        page_length: int,
        **kwargs,
    ) -> tuple[list[utils.ExperimentDict], int]:
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
            BackEndDatabaseError: If the database query returns a None when counting
                the number of experiments.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of experiments")

        filters = list()

        if group_id is not None:
            filters.append(models.Resource.group_id == group_id)

        if search_string:
            filters.append(
                construct_sql_query_filters(search_string, SEARCHABLE_FIELDS)
            )

        stmt = (
            select(func.count(models.Experiment.resource_id))
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.Experiment.resource_snapshot_id,
            )
        )
        total_num_experiments = db.session.scalars(stmt).first()

        if total_num_experiments is None:
            log.error(
                "The database query returned a None when counting the number of "
                "experiments when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        if total_num_experiments == 0:
            return cast(list[utils.ExperimentDict], []), total_num_experiments

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

        entrypoint_ids = {
            resource.resource_id: experiment.resource_id
            for experiment in experiments
            for resource in experiment.children
            if resource.resource_type == "entry_point" and not resource.is_deleted
        }
        entrypoints = self._entrypoint_ids_service.get(
            list(entrypoint_ids.keys()), error_if_not_found=True, log=log
        )
        entrypoints_dict = {
            entrypoint.resource_id: entrypoint for entrypoint in entrypoints
        }

        drafts_stmt = select(
            models.DraftResource.payload["resource_id"].as_string().cast(Integer)
        ).where(
            models.DraftResource.payload["resource_id"]
            .as_string()
            .cast(Integer)
            .in_(tuple(experiment.resource_id for experiment in experiments)),
            models.DraftResource.user_id == current_user.user_id,
        )
        experiments_dict: dict[int, utils.ExperimentDict] = {
            experiment.resource_id: utils.ExperimentDict(
                experiment=experiment, entrypoints=[], queue=None, has_draft=False
            )
            for experiment in experiments
        }
        for resource_id in db.session.scalars(drafts_stmt):
            experiments_dict[resource_id]["has_draft"] = True
        for experiment_dict in experiments_dict.values():
            for resource in experiment_dict["experiment"].children:
                if resource.resource_type == "entry_point" and not resource.is_deleted:
                    entrypoint = entrypoints_dict[resource.resource_id]
                    experiment_dict["entrypoints"].append(entrypoint)

        return list(experiments_dict.values()), total_num_experiments


class ExperimentIdService(object):
    """The service methods for registering and managing experiments by their unique
    id.
    """

    @inject
    def __init__(
        self,
        entrypoint_ids_service: EntrypointIdsService,
        experiment_name_service: ExperimentNameService,
    ) -> None:
        """Initialize the experiment service.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_ids_service: An EntrypointIdsService object.
            experiment_name_service: An ExperimentNameService object.
        """
        self._entrypoint_ids_service = entrypoint_ids_service
        self._experiment_name_service = experiment_name_service

    def get(
        self,
        experiment_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> utils.ExperimentDict | None:
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

        entrypoint_ids = [
            resource.resource_id
            for resource in experiment.children
            if resource.resource_type == "entry_point" and not resource.is_deleted
        ]
        entrypoints = self._entrypoint_ids_service.get(
            entrypoint_ids, error_if_not_found=True, log=log
        )

        drafts_stmt = (
            select(models.DraftResource.draft_resource_id)
            .where(
                models.DraftResource.payload["resource_id"].as_string().cast(Integer)
                == experiment.resource_id,
                models.DraftResource.user_id == current_user.user_id,
            )
            .exists()
            .select()
        )
        has_draft = db.session.scalar(drafts_stmt)

        return utils.ExperimentDict(
            experiment=experiment,
            entrypoints=entrypoints,
            queue=None,
            has_draft=has_draft,
        )

    def modify(
        self,
        experiment_id: int,
        name: str,
        description: str,
        entrypoint_ids: list[int],
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> utils.ExperimentDict | None:
        """Modify an experiment.

        Args:
            experiment_id: The unique if of the experiment.
            name: The new name of the experiment.
            description: The new description of the experiment.
            entrypoint_ids: The new entrypoints of the experiment.
            error_if_not_found: If True, raise an error if the experiment is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated experiment object.

        Raises:
            ExperimentDoesNotExistError: If the experiment is not found and
                `error_if_not_found` is True.
            ExperimentAlreadyExistsError: If the experiment name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        experiment_dict = self.get(
            experiment_id, error_if_not_found=error_if_not_found, log=log
        )

        if experiment_dict is None:
            return None

        experiment = experiment_dict["experiment"]
        group_id = experiment.resource.group_id
        if (
            name != experiment.name
            and self._experiment_name_service.get(name, group_id=group_id, log=log)
            is not None
        ):
            log.debug("Experiment name already exists", name=name, group_id=group_id)
            raise ExperimentAlreadyExistsError

        entrypoints = self._entrypoint_ids_service.get(
            entrypoint_ids, error_if_not_found=True, log=log
        )

        new_experiment = models.Experiment(
            name=name,
            description=description,
            resource=experiment.resource,
            creator=current_user,
        )
        new_experiment.children = [entrypoint.resource for entrypoint in entrypoints]
        db.session.add(new_experiment)

        if commit:
            db.session.commit()
            log.debug(
                "Experiment modification successful",
                experiment_id=experiment_id,
                name=name,
            )

        return utils.ExperimentDict(
            experiment=new_experiment,
            entrypoints=entrypoints,
            queue=None,
            has_draft=False,
        )

    def delete(self, experiment_id: int, **kwargs) -> dict[str, Any]:
        """Delete an experiment.

        Args:
            experiment_id: The unqiue id of the experiment.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        stmt = select(models.Resource).filter_by(
            resource_id=experiment_id, resource_type=RESOURCE_TYPE, is_deleted=False
        )
        experiment_resource = db.session.scalars(stmt).first()

        if experiment_resource is None:
            raise ExperimentDoesNotExistError

        deleted_resource_lock = models.ResourceLock(
            resource_lock_type=resource_lock_types.DELETE,
            resource=experiment_resource,
        )
        db.session.add(deleted_resource_lock)
        db.session.commit()
        log.debug("Experiment deleted", experiment_id=experiment_id)

        return {"status": "Success", "id": [experiment_id]}


class ExperimentIdEntrypointsService(object):
    """The service methods for managing entrypoints attached to an experiment."""

    @inject
    def __init__(
        self,
        experiment_id_service: ExperimentIdService,
        entrypoint_ids_service: EntrypointIdsService,
    ) -> None:
        """Initialize the experiment service.

        All arguments are provided via dependency injection.

        Args:
            experiment_id_service: A ExperimentIdService object.
            entrypoint_ids_service: A EntrypointIdsService object.
        """
        self._experiment_id_service = experiment_id_service
        self._entrypoint_ids_service = entrypoint_ids_service

    def get(
        self,
        experiment_id: int,
        **kwargs,
    ) -> list[models.EntryPoint]:
        """Fetch the list of entrypoints for an experiment.

        Args:
            experiment_id: The unique id of the experiment.
            error_if_not_found: If True, raise an error if the experiment is not found.
                Defaults to False.

        Returns:
            The list of plugins.

        Raises:
            ExperimentDoesNotExistError: If the experiment is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Get entrypoints for an experiment by resource id",
            resource_id=experiment_id,
        )

        experiment_dict = cast(
            utils.ExperimentDict,
            self._experiment_id_service.get(
                experiment_id, error_if_not_found=True, log=log
            ),
        )
        return experiment_dict["entrypoints"]

    def append(
        self,
        experiment_id: int,
        entrypoint_ids: list[int],
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> list[models.EntryPoint] | None:
        """Append one or more Entrypoints to an experiment

        Args:
            experiment_id: The unique id of the experiment.
            entrypoint_ids: The list of entrypoint ids to append.
            error_if_not_found: If True, raise an error if the resource is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated list of entrypoints resource objects.

        Raises:
            ExperimentDoesNotExistError: If the resource is not found and
                `error_if_not_found` is True.
            EntrypointDoesNotExistError: If one or more entrypoints are not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Append entrypoints to an experiment by resource id",
            resource_id=experiment_id,
        )

        experiment_dict = cast(
            utils.ExperimentDict,
            self._experiment_id_service.get(
                experiment_id, error_if_not_found=True, log=log
            ),
        )
        experiment = experiment_dict["experiment"]
        entrypoints = experiment_dict["entrypoints"]

        existing_entrypoint_ids = set(
            resource.resource_id for resource in experiment.children
        )
        new_entrypoint_ids = set(entrypoint_ids) - existing_entrypoint_ids
        new_entrypoints = self._entrypoint_ids_service.get(
            list(new_entrypoint_ids), error_if_not_found=True, log=log
        )
        if error_if_not_found and len(new_entrypoints) != len(new_entrypoint_ids):
            found_entrypoint_ids = set(
                entrypoint.resource_id for entrypoint in new_entrypoints
            )
            missing_entrypoint_ids = new_entrypoint_ids - found_entrypoint_ids
            log.debug(entrypoint_ids=list(missing_entrypoint_ids))
            raise EntrypointDoesNotExistError

        experiment.children.extend(
            [entrypoint.resource for entrypoint in new_entrypoints]
        )

        if commit:
            db.session.commit()
            log.debug(
                "Entrypoints appended successfully", entrypoint_ids=entrypoint_ids
            )

        return entrypoints + new_entrypoints

    def modify(
        self,
        experiment_id: int,
        entrypoint_ids: list[int],
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> list[models.EntryPoint]:
        """Modify the list of entrypoints for an experiment.

        Args:
            experiment_id: The unique id of the experiment.
            entrypoint_ids: The list of entrypoint ids to append.
            error_if_not_found: If True, raise an error if the resource is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated entrypoint resource object.

        Raises:
            ResourceDoesNotExistError: If the resource is not found and
                `error_if_not_found` is True.
            EntrypointDoesNotExistError: If one or more entrypoints are not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        experiment_dict = cast(
            utils.ExperimentDict,
            self._experiment_id_service.get(
                experiment_id, error_if_not_found=True, log=log
            ),
        )
        experiment = experiment_dict["experiment"]

        entrypoints = self._entrypoint_ids_service.get(
            entrypoint_ids, error_if_not_found=True, log=log
        )

        experiment.children = [entrypoint.resource for entrypoint in entrypoints]

        if commit:
            db.session.commit()
            log.debug(
                "Experiment entrypoints updated successfully",
                entrypoint_ids=entrypoint_ids,
            )

        return entrypoints

    def delete(self, experiment_id: int, **kwargs) -> dict[str, Any]:
        """Remove entrypoints from an experiment.

        Args:
            experiment_id: The unique id of the experiment.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        experiment_dict = cast(
            utils.ExperimentDict,
            self._experiment_id_service.get(
                experiment_id, error_if_not_found=True, log=log
            ),
        )
        experiment = experiment_dict["experiment"]
        experiment.children = []

        entrypoint_ids = [
            entrypoint.resource_id for entrypoint in experiment_dict["entrypoints"]
        ]

        db.session.commit()
        log.debug(
            "Entrypoints removed from experiment",
            experiment_id=experiment_id,
            entrypoint_ids=entrypoint_ids,
        )

        return {"status": "Success", "id": entrypoint_ids}


class ExperimentIdEntrypointsIdService(object):
    """The service methods for removing a entrypoint attached to an experiment."""

    @inject
    def __init__(
        self,
        experiment_id_service: ExperimentIdService,
    ) -> None:
        """Initialize the experiment service.

        All arguments are provided via dependency injection.

        Args:
            experiment_id_service: A ExperimentIdService object.
        """
        self._experiment_id_service = experiment_id_service

    def delete(self, experiment_id: int, entrypoint_id, **kwargs) -> dict[str, Any]:
        """Remove a entrypoint from an experiment.

        Args:
            experiment_id: The unique id of the experiment.
            entrypoint_id: The unique id of the entrypoint.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        experiment_dict = cast(
            utils.ExperimentDict,
            self._experiment_id_service.get(
                experiment_id, error_if_not_found=True, log=log
            ),
        )
        experiment = experiment_dict["experiment"]

        entrypoint_resources = {
            resource.resource_id: resource for resource in experiment.children
        }

        removed_entrypoint = entrypoint_resources.pop(entrypoint_id, None)

        if removed_entrypoint is None:
            raise EntrypointDoesNotExistError

        experiment.children = list(entrypoint_resources.values())

        db.session.commit()
        log.debug(
            "Entrypoint removed",
            experiment_id=experiment_id,
            entrypoint_id=entrypoint_id,
        )

        return {"status": "Success", "id": [entrypoint_id]}


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
