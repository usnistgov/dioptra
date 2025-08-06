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

from typing import Any, Final

import structlog
from flask_login import current_user
from injector import inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.db.repository.utils import DeletionPolicy
from dioptra.restapi.db.unit_of_work import UnitOfWork
from dioptra.restapi.errors import EntityDoesNotExistError
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.entity_types import EntityTypes
from dioptra.restapi.v1.entrypoints.service import EntrypointIdsService
from dioptra.restapi.v1.shared.search_parser import parse_search_text

LOGGER: BoundLogger = structlog.stdlib.get_logger()

EXPERIMENT_RESOURCE_TYPE: Final[EntityTypes] = EntityTypes.EXPERIMENT


class ExperimentService(object):
    """The service methods for registering and managing experiments by their unique
    id."""

    @inject
    def __init__(
        self,
        entrypoint_ids_service: EntrypointIdsService,
        uow: UnitOfWork,
    ) -> None:
        """Initialize the experiment service.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_ids_service: An EntrypointIdsService object.
            uow: A UnitOfWork instance
        """
        self._entrypoint_ids_service = entrypoint_ids_service
        self._uow = uow

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
            EntityExistsError: If an experiment with the given name already
                exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        owner = self._uow.group_repo.get_one(group_id, DeletionPolicy.NOT_DELETED)

        resource = models.Resource(EXPERIMENT_RESOURCE_TYPE.get_db_schema_name(), owner)
        new_experiment = models.Experiment(
            description,
            resource,
            current_user,
            name,
        )

        entrypoints = (
            self._entrypoint_ids_service.get(
                entrypoint_ids, error_if_not_found=True, log=log
            )
            if entrypoint_ids is not None
            else []
        )
        new_experiment.children.extend(
            entrypoint.resource for entrypoint in entrypoints
        )

        try:
            self._uow.experiment_repo.create(new_experiment)
        except Exception:
            self._uow.rollback()
            raise

        if commit:
            self._uow.commit()
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
        sort_by_string: str,
        descending: bool,
        **kwargs,
    ) -> tuple[list[utils.ExperimentDict], int]:
        """Fetch a list of experiments, optionally filtering by search string and paging
        parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first page to be returned.
            page_length: The maximum number of experiments to be returned.
            sort_by_string: The name of the column to sort.
            descending: Boolean indicating whether to sort by descending or not.

        Returns:
            A tuple containing a list of experiments and the total number of experiments
            matching the query.

        Raises:
            BackEndDatabaseError: If the database query returns a None when counting
                the number of experiments.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of experiments")

        search_struct = parse_search_text(search_string)

        experiments, total_num_experiments = (
            self._uow.experiment_repo.get_by_filters_paged(
                group_id,
                search_struct,
                page_index,
                page_length,
                sort_by_string,
                descending,
                DeletionPolicy.NOT_DELETED,
            )
        )

        experiments_dict: dict[int, utils.ExperimentDict] = {
            experiment.resource_id: utils.ExperimentDict(
                experiment=experiment,
                # TypedDict requires a list specifically
                entrypoints=list(
                    self._uow.experiment_repo.get_entrypoints(
                        experiment,
                        DeletionPolicy.NOT_DELETED,
                    )
                ),
                queue=None,
                has_draft=False,
            )
            for experiment in experiments
        }

        resource_ids_with_drafts = self._uow.drafts_repo.has_draft_modifications(
            experiments,
            current_user,
        )
        for resource_id in resource_ids_with_drafts:
            experiments_dict[resource_id]["has_draft"] = True

        return list(experiments_dict.values()), total_num_experiments


class ExperimentIdService(object):
    """The service methods for registering and managing experiments by their unique
    id.
    """

    @inject
    def __init__(
        self,
        entrypoint_ids_service: EntrypointIdsService,
        uow: UnitOfWork,
    ) -> None:
        """Initialize the experiment service.

        All arguments are provided via dependency injection.

        Args:
            entrypoint_ids_service: An EntrypointIdsService object.
            uow: A UnitOfWork instance
        """
        self._entrypoint_ids_service = entrypoint_ids_service
        self._uow = uow

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
            EntityDoesNotExistError: If the experiment is not found and if
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get experiment by id", experiment_id=experiment_id)

        experiment = self._uow.experiment_repo.get(
            experiment_id,
            DeletionPolicy.NOT_DELETED,
        )

        if experiment is None:
            if error_if_not_found:
                raise EntityDoesNotExistError(
                    EXPERIMENT_RESOURCE_TYPE, experiment_id=experiment_id
                )

            return None

        entrypoints = self._uow.experiment_repo.get_entrypoints(
            experiment,
            DeletionPolicy.NOT_DELETED,
        )

        has_draft = self._uow.drafts_repo.has_draft_modification(
            experiment,
            current_user,
        )

        return utils.ExperimentDict(
            experiment=experiment,
            # TypedDict requires a list specifically
            entrypoints=list(entrypoints),
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
            EntityDoesNotExistError: If the experiment is not found and
                `error_if_not_found` is True.
            EntityExistsError: If the experiment name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        experiment = self._uow.experiment_repo.get(
            experiment_id,
            DeletionPolicy.ANY,
        )

        if not experiment:
            if error_if_not_found:
                raise EntityDoesNotExistError(
                    EXPERIMENT_RESOURCE_TYPE, resource_id=experiment_id
                )
            else:
                return None
        elif experiment.resource.is_deleted:
            if error_if_not_found:
                # treat "deleted" as if "not found"?
                raise EntityDoesNotExistError(
                    EXPERIMENT_RESOURCE_TYPE, resource_id=experiment_id
                )
            else:
                return None

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

        try:
            self._uow.experiment_repo.create_snapshot(new_experiment)
        except Exception:
            self._uow.rollback()
            raise

        if commit:
            self._uow.commit()

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
            experiment_id: The unique id of the experiment.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        with self._uow:
            self._uow.experiment_repo.delete(experiment_id)
        log.debug("Experiment deleted", experiment_id=experiment_id)

        return {"status": "Success", "id": [experiment_id]}


class ExperimentIdEntrypointsService(object):
    """The service methods for managing entrypoints attached to an experiment."""

    @inject
    def __init__(
        self,
        uow: UnitOfWork,
    ) -> None:
        """Initialize the experiment service.

        All arguments are provided via dependency injection.

        Args:
            uow: A UnitOfWork instance
        """
        self._uow = uow

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
            EntityDoesNotExistError: If the experiment is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Get entrypoints for an experiment by resource id",
            resource_id=experiment_id,
        )

        return list(
            self._uow.experiment_repo.get_entrypoints(
                experiment_id,
                DeletionPolicy.NOT_DELETED,
            )
        )

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
            EntityDoesNotExistError: If the experiment is not found and
                `error_if_not_found` is True.
            EntityDoesNotExistError: If one or more entrypoints are not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug(
            "Append entrypoints to an experiment by resource id",
            resource_id=experiment_id,
        )

        try:
            all_children = self._uow.experiment_repo.add_entrypoints(
                experiment_id,
                entrypoint_ids,
            )
        except Exception:
            self._uow.rollback()
            raise

        if commit:
            self._uow.commit()

        log.debug("Entrypoints appended successfully", entrypoint_ids=entrypoint_ids)
        return all_children

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
            EntityDoesNotExistError: If the resource is not found and
                `error_if_not_found` is True.
            EntityDoesNotExistError: If one or more entrypoints are not found.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        try:
            entrypoints = self._uow.experiment_repo.set_entrypoints(
                experiment_id,
                entrypoint_ids,
            )
        except Exception:
            self._uow.rollback()
            raise

        if commit:
            self._uow.commit()
            log.debug(
                "Experiment entrypoints updated successfully",
                entrypoint_ids=entrypoint_ids,
            )

        return list(entrypoints)

    def delete(self, experiment_id: int, **kwargs) -> dict[str, Any]:
        """Remove entrypoints from an experiment.

        Args:
            experiment_id: The unique id of the experiment.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        experiment = self._uow.experiment_repo.get_one(
            experiment_id,
            DeletionPolicy.NOT_DELETED,
        )

        entrypoint_ids = [child.resource_id for child in experiment.children]

        with self._uow:
            experiment.children = []

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
        uow: UnitOfWork,
    ) -> None:
        """Initialize the experiment service.

        All arguments are provided via dependency injection.

        Args:
            uow: A UnitOfWork instance
        """
        self._uow = uow

    def delete(self, experiment_id: int, entrypoint_id, **kwargs) -> dict[str, Any]:
        """Remove a entrypoint from an experiment.

        Args:
            experiment_id: The unique id of the experiment.
            entrypoint_id: The unique id of the entrypoint.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        with self._uow:
            self._uow.experiment_repo.unlink_entrypoint(experiment_id, entrypoint_id)

        log.debug(
            "Entrypoint removed",
            experiment_id=experiment_id,
            entrypoint_id=entrypoint_id,
        )

        return {"status": "Success", "id": [entrypoint_id]}
