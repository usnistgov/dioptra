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
"""The server-side functions that perform model endpoint operations."""
from __future__ import annotations

from typing import Any, Final, cast

import structlog
from flask_login import current_user
from injector import inject
from sqlalchemy import Integer, func, select
from sqlalchemy.orm import aliased
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import db, models
from dioptra.restapi.errors import BackendDatabaseError
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.artifacts.service import ArtifactIdService
from dioptra.restapi.v1.groups.service import GroupIdService
from dioptra.restapi.v1.shared.search_parser import construct_sql_query_filters

from .errors import (
    ModelAlreadyExistsError,
    ModelDoesNotExistError,
    ModelVersionDoesNotExistError,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

MODEL_RESOURCE_TYPE: Final[str] = "ml_model"
MODEL_VERSION_RESOURCE_TYPE: Final[str] = "ml_model_version"
MODEL_SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "name": lambda x: models.MlModel.name.like(x, escape="/"),
    "description": lambda x: models.MlModel.description.like(x, escape="/"),
}
MODEL_VERSION_SEARCHABLE_FIELDS: Final[dict[str, Any]] = {
    "description": lambda x: models.MlModelVersion.description.like(x, escape="/"),
}


class ModelService(object):
    """The service methods for registering and managing models by their unique id."""

    @inject
    def __init__(
        self,
        model_name_service: ModelNameService,
        group_id_service: GroupIdService,
    ) -> None:
        """Initialize the model service.

        All arguments are provided via dependency injection.

        Args:
            model_name_service: A ModelNameService object.
            group_id_service: A GroupIdService object.
        """
        self._model_name_service = model_name_service
        self._group_id_service = group_id_service

    def create(
        self,
        name: str,
        description: str,
        group_id: int,
        commit: bool = True,
        **kwargs,
    ) -> utils.ModelWithVersionDict:
        """Create a new model.

        Args:
            name: The name of the model. The combination of name and group_id must be
                unique.
            description: The description of the model.
            group_id: The group that will own the model.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created model object.

        Raises:
            ModelAlreadyExistsError: If a model with the given name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        if self._model_name_service.get(name, group_id=group_id, log=log) is not None:
            log.debug("Model name already exists", name=name, group_id=group_id)
            raise ModelAlreadyExistsError

        group = self._group_id_service.get(group_id, error_if_not_found=True)

        resource = models.Resource(resource_type=MODEL_RESOURCE_TYPE, owner=group)

        ml_model = models.MlModel(
            name=name,
            description=description,
            resource=resource,
            creator=current_user,
        )

        db.session.add(ml_model)

        if commit:
            db.session.commit()
            log.debug(
                "Model registration successful",
                model_id=ml_model.resource_id,
                name=ml_model.name,
            )

        return utils.ModelWithVersionDict(
            ml_model=ml_model, version=None, has_draft=False
        )

    def get(
        self,
        group_id: int | None,
        search_string: str,
        page_index: int,
        page_length: int,
        **kwargs,
    ) -> Any:
        """Fetch a list of models, optionally filtering by search string and paging
        parameters.

        Args:
            group_id: A group ID used to filter results.
            search_string: A search string used to filter results.
            page_index: The index of the first group to be returned.
            page_length: The maximum number of models to be returned.

        Returns:
            A tuple containing a list of models and the total number of models matching
            the query.

        Raises:
            SearchNotImplementedError: If a search string is provided.
            BackendDatabaseError: If the database query returns a None when counting
                the number of models.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get full list of models")

        filters = list()

        if group_id is not None:
            filters.append(models.Resource.group_id == group_id)

        if search_string:
            filters.append(
                construct_sql_query_filters(search_string, MODEL_SEARCHABLE_FIELDS)
            )

        stmt = (
            select(func.count(models.MlModel.resource_id))
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.MlModel.resource_snapshot_id,
            )
        )
        total_num_ml_models = db.session.scalars(stmt).first()

        if total_num_ml_models is None:
            log.error(
                "The database query returned a None when counting the number of "
                "groups when it should return a number.",
                sql=str(stmt),
            )
            raise BackendDatabaseError

        if total_num_ml_models == 0:
            return [], total_num_ml_models

        latest_ml_models_stmt = (
            select(models.MlModel)
            .join(models.Resource)
            .where(
                *filters,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.MlModel.resource_snapshot_id,
            )
            .offset(page_index)
            .limit(page_length)
        )
        ml_models = db.session.scalars(latest_ml_models_stmt).all()

        # extract list of model ids
        model_ids = [ml_model.resource_id for ml_model in ml_models]

        # Build CTE that retrieves all snapshot ids for the list of ml model versions
        # associated with retrieved ml models
        parent_model = aliased(models.MlModel)
        model_version_snapshot_ids_cte = (
            select(models.MlModelVersion.resource_snapshot_id)
            .join(
                models.resource_dependencies_table,
                models.MlModelVersion.resource_id
                == models.resource_dependencies_table.c.child_resource_id,
            )
            .join(
                parent_model,
                parent_model.resource_id
                == models.resource_dependencies_table.c.parent_resource_id,
            )
            .where(parent_model.resource_id.in_(model_ids))
            .cte()
        )

        # get the latest model version snapshots associated with the retrieved models
        latest_model_versions_stmt = (
            select(models.MlModelVersion)
            .join(models.Resource)
            .where(
                models.MlModelVersion.resource_snapshot_id.in_(
                    select(model_version_snapshot_ids_cte)
                ),
                models.Resource.latest_snapshot_id
                == models.MlModelVersion.resource_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
            .order_by(models.MlModelVersion.created_on)
        )
        model_versions = db.session.scalars(latest_model_versions_stmt).unique().all()

        # build a dictionary structure to re-associate models with model versions
        models_dict: dict[int, utils.ModelWithVersionDict] = {
            model.resource_id: utils.ModelWithVersionDict(
                ml_model=model, version=None, has_draft=False
            )
            for model in ml_models
        }
        for model_version in model_versions:
            models_dict[model_version.model_id]["version"] = model_version

        drafts_stmt = select(
            models.DraftResource.payload["resource_id"].as_string().cast(Integer)
        ).where(
            models.DraftResource.payload["resource_id"]
            .as_string()
            .cast(Integer)
            .in_(
                tuple(model["ml_model"].resource_id for model in models_dict.values())
            ),
            models.DraftResource.user_id == current_user.user_id,
        )
        for resource_id in db.session.scalars(drafts_stmt):
            models_dict[resource_id]["has_draft"] = True

        return list(models_dict.values()), total_num_ml_models


class ModelIdService(object):
    """The service methods for registering and managing models by their unique id."""

    @inject
    def __init__(
        self,
        model_name_service: ModelNameService,
    ) -> None:
        """Initialize the model service.

        All arguments are provided via dependency injection.

        Args:
            model_name_service: A ModelNameService object.
        """
        self._model_name_service = model_name_service

    def get(
        self,
        model_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> utils.ModelWithVersionDict | None:
        """Fetch a model by its unique id.

        Args:
            model_id: The unique id of the model.
            error_if_not_found: If True, raise an error if the model is not found.
                Defaults to False.

        Returns:
            The model object if found, otherwise None.

        Raises:
            ModelDoesNotExistError: If the model is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get model by id", model_id=model_id)

        stmt = (
            select(models.MlModel)
            .join(models.Resource)
            .where(
                models.MlModel.resource_id == model_id,
                models.MlModel.resource_snapshot_id
                == models.Resource.latest_snapshot_id,
                models.Resource.is_deleted == False,  # noqa: E712
            )
        )
        ml_model = db.session.scalars(stmt).first()

        if ml_model is None:
            if error_if_not_found:
                log.debug("Model not found", model_id=model_id)
                raise ModelDoesNotExistError

            return None

        latest_ml_model_version_stmt = (
            select(models.MlModelVersion)
            .join(models.Resource)
            .where(
                models.MlModelVersion.model_id == model_id,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.MlModelVersion.resource_snapshot_id,
            )
            .order_by(models.MlModelVersion.created_on.desc())
            .limit(1)
        )
        latest_version = db.session.scalar(latest_ml_model_version_stmt)

        drafts_stmt = (
            select(models.DraftResource.draft_resource_id)
            .where(
                models.DraftResource.payload["resource_id"].as_string().cast(Integer)
                == ml_model.resource_id,
                models.DraftResource.user_id == current_user.user_id,
            )
            .exists()
            .select()
        )
        has_draft = db.session.scalar(drafts_stmt)

        return utils.ModelWithVersionDict(
            ml_model=ml_model, version=latest_version, has_draft=has_draft
        )

    def modify(
        self,
        model_id: int,
        name: str,
        description: str,
        error_if_not_found: bool = False,
        commit: bool = True,
        **kwargs,
    ) -> utils.ModelWithVersionDict | None:
        """Modify a model.

        Args:
            model_id: The unique id of the model.
            name: The new name of the model.
            description: The new description of the model.
            error_if_not_found: If True, raise an error if the group is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated model object.

        Raises:
            ModelDoesNotExistError: If the model is not found and `error_if_not_found`
                is True.
            ModelAlreadyExistsError: If the model name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        ml_model_dict = self.get(
            model_id, error_if_not_found=error_if_not_found, log=log
        )

        if ml_model_dict is None:
            if error_if_not_found:
                raise ModelDoesNotExistError

            return None

        ml_model = ml_model_dict["ml_model"]
        version = ml_model_dict["version"]
        has_draft = ml_model_dict["has_draft"]

        group_id = ml_model.resource.group_id
        if (
            name != ml_model.name
            and self._model_name_service.get(name, group_id=group_id, log=log)
            is not None
        ):
            log.debug("Model name already exists", name=name, group_id=group_id)
            raise ModelAlreadyExistsError

        new_ml_model = models.MlModel(
            name=name,
            description=description,
            resource=ml_model.resource,
            creator=current_user,
        )
        db.session.add(new_ml_model)

        if commit:
            db.session.commit()
            log.debug(
                "Model modification successful",
                model_id=model_id,
                name=name,
                description=description,
            )

        return utils.ModelWithVersionDict(
            ml_model=new_ml_model,
            version=version,
            has_draft=has_draft,
        )

    def delete(self, model_id: int, **kwargs) -> dict[str, Any]:
        """Delete a model.

        Args:
            model_id: The unique id of the model.

        Returns:
            A dictionary reporting the status of the request.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        stmt = select(models.Resource).filter_by(
            resource_id=model_id, resource_type=MODEL_RESOURCE_TYPE, is_deleted=False
        )
        model_resource = db.session.scalars(stmt).first()

        if model_resource is None:
            raise ModelDoesNotExistError

        deleted_resource_lock = models.ResourceLock(
            resource_lock_type="delete",
            resource=model_resource,
        )
        db.session.add(deleted_resource_lock)
        db.session.commit()
        log.debug("Model deleted", model_id=model_id)

        return {"status": "Success", "model_id": model_id}


class ModelIdVersionsService(object):
    @inject
    def __init__(
        self,
        artifact_id_service: ArtifactIdService,
        model_id_service: ModelIdService,
    ) -> None:
        """Initialize the model service.

        All arguments are provided via dependency injection.

        Args:
            artifact_id_service: A ArtifactIdService object.
            model_id_service: A ModelIdService object.
        """
        self._artifact_id_service = artifact_id_service
        self._model_id_service = model_id_service

    def create(
        self,
        model_id: int,
        description: str,
        artifact_id: int,
        commit: bool = True,
        **kwargs,
    ) -> utils.ModelWithVersionDict:
        """Create a new model version.

        Args:
            model_id: The unique id of the model.
            description: The description of the model version.
            artifact_id: The artifact for the model version.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The newly created model object.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        ml_model_dict = cast(
            utils.ModelWithVersionDict,
            self._model_id_service.get(model_id, error_if_not_found=True, log=log),
        )
        ml_model = ml_model_dict["ml_model"]
        has_draft = ml_model_dict["has_draft"]
        version = ml_model_dict["version"]
        next_version_number = version.version_number + 1 if version is not None else 1
        group = ml_model.resource.owner
        artifact_dict = cast(
            utils.ArtifactDict,
            self._artifact_id_service.get(
                artifact_id, error_if_not_found=True, log=log
            ),
        )
        artifact = artifact_dict["artifact"]

        resource = models.Resource(
            resource_type=MODEL_VERSION_RESOURCE_TYPE, owner=group
        )
        new_version = models.MlModelVersion(
            description=description,
            artifact=artifact,
            version_number=next_version_number,
            resource=resource,
            creator=current_user,
        )

        ml_model.resource.children.append(new_version.resource)
        db.session.add(new_version)

        if commit:
            db.session.commit()
            log.debug(
                "Model registration successful",
                model_id=ml_model.resource_id,
                name=ml_model.name,
            )

        return utils.ModelWithVersionDict(
            ml_model=ml_model,
            version=new_version,
            has_draft=has_draft,
        )

    def get(
        self,
        model_id: int,
        search_string: str,
        page_index: int,
        page_length: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> tuple[list[utils.ModelWithVersionDict], int] | None:
        """Fetch a list of versions of a model.

        Args:
            model_id: The unique id of the resource.
            search_string: A search string used to filter results.
            page_index: The index of the first snapshot to be returned.
            page_length: The maximum number of versions to be returned.
            error_if_not_found: If True, raise an error if the resource is not found.
                Defaults to False.

        Returns:
            The list of resource versions of the resource object if found, otherwise
                None.

        Raises:
            ResourceDoesNotExistError: If the resource is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get model versions by id", model_id=model_id)

        ml_model_dict = cast(
            utils.ModelWithVersionDict,
            self._model_id_service.get(model_id, error_if_not_found=True, log=log),
        )
        ml_model = ml_model_dict["ml_model"]
        model_id = ml_model.resource_id

        filters = construct_sql_query_filters(
            search_string, MODEL_VERSION_SEARCHABLE_FIELDS
        )

        latest_model_versions_count_stmt = (
            select(func.count(models.MlModelVersion.resource_id))
            .join(models.Resource)
            .where(
                filters,
                models.MlModelVersion.model_id == model_id,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.MlModelVersion.resource_snapshot_id,
            )
        )
        total_num_model_versions = db.session.scalar(latest_model_versions_count_stmt)

        if total_num_model_versions is None:
            log.error(
                "The database query returned a None when counting the number of "
                "groups when it should return a number.",
                sql=str(total_num_model_versions),
            )
            raise BackendDatabaseError

        if total_num_model_versions == 0:
            return [], total_num_model_versions

        latest_model_versions_stmt = (
            select(models.MlModelVersion)
            .join(models.Resource)
            .where(
                filters,
                models.MlModelVersion.model_id == model_id,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.MlModelVersion.resource_snapshot_id,
            )
            .offset(page_index)
            .limit(page_length)
        )

        drafts_stmt = (
            select(
                models.DraftResource.payload["resource_id"].as_string().cast(Integer)
            )
            .where(
                models.DraftResource.payload["resource_id"].as_string().cast(Integer)
                == model_id,
                models.DraftResource.user_id == current_user.user_id,
            )
            .exists()
            .select()
        )
        has_draft = db.session.scalar(drafts_stmt)

        return [
            utils.ModelWithVersionDict(
                ml_model=ml_model, version=version, has_draft=has_draft
            )
            for version in db.session.scalars(latest_model_versions_stmt).unique().all()
        ], total_num_model_versions


class ModelIdVersionsNumberService(object):
    @inject
    def __init__(
        self,
        model_id_service: ModelIdService,
    ) -> None:
        """Initialize the model service.

        All arguments are provided via dependency injection.

        Args:
            model_id_service: A ModelIdService object.
        """
        self._model_id_service = model_id_service

    def get(
        self,
        model_id: int,
        version_number: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> utils.ModelWithVersionDict | None:
        """Fetch a specific version of a Model resource.

        Args:
            model_id: The unique id of the Model resource.
            version_number: The version number of the Model
            error_if_not_found: If True, raise an error if the resource is not found.
                Defaults to False.

        Returns:
            The requested version the resource object if found, otherwise None.

        Raises:
            ResourceDoesNotExistError: If the resource is not found and
                `error_if_not_found` is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get resource snapshot by id", model_id=model_id)

        ml_model_dict = self._model_id_service.get(
            model_id, error_if_not_found=error_if_not_found, log=log
        )

        if ml_model_dict is None:
            return None

        ml_model = ml_model_dict["ml_model"]

        ml_model_version_stmt = (
            select(models.MlModelVersion)
            .join(models.Resource)
            .where(
                models.MlModelVersion.model_id == model_id,
                models.MlModelVersion.version_number == version_number,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.MlModelVersion.resource_snapshot_id,
            )
        )
        latest_version = db.session.scalar(ml_model_version_stmt)

        if latest_version is None:
            if error_if_not_found:
                log.debug("Model version not found", version_number=version_number)
                raise ModelVersionDoesNotExistError

            return None

        return utils.ModelWithVersionDict(
            ml_model=ml_model, version=latest_version, has_draft=False
        )

    def modify(
        self,
        model_id: int,
        version_number: int,
        description: str,
        commit: bool = True,
        **kwargs,
    ) -> utils.ModelWithVersionDict | None:
        """Modify a model version.

        Args:
            model_id: The unique id of the model.
            version_number: The version number of the model.
            description: The new description of the model version.
            error_if_not_found: If True, raise an error if the group is not found.
                Defaults to False.
            commit: If True, commit the transaction. Defaults to True.

        Returns:
            The updated model object.

        Raises:
            ModelDoesNotExistError: If the model is not found and `error_if_not_found`
                is True.
            ModelAlreadyExistsError: If the model name already exists.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())

        ml_model_dict = cast(
            utils.ModelWithVersionDict,
            self.get(model_id, version_number, error_if_not_found=True, log=log),
        )

        ml_model = ml_model_dict["ml_model"]
        version = cast(models.MlModelVersion, ml_model_dict["version"])

        new_version = models.MlModelVersion(
            description=description,
            artifact=version.artifact,
            version_number=version.version_number,
            resource=version.resource,
            creator=current_user,
        )
        db.session.add(new_version)

        if commit:
            db.session.commit()
            log.debug(
                "Model Version modification successful",
                model_id=model_id,
                version_number=version_number,
                description=description,
            )

        return utils.ModelWithVersionDict(
            ml_model=ml_model,
            version=new_version,
            has_draft=False,
        )


class ModelNameService(object):
    """The service methods for managing models by their name."""

    def get(
        self,
        name: str,
        group_id: int,
        error_if_not_found: bool = False,
        **kwargs,
    ) -> models.MlModel | None:
        """Fetch a model by its name.

        Args:
            name: The name of the model.
            group_id: The the group id of the model.
            error_if_not_found: If True, raise an error if the model is not found.
                Defaults to False.

        Returns:
            The model object if found, otherwise None.

        Raises:
            ModelDoesNotExistError: If the model is not found and `error_if_not_found`
                is True.
        """
        log: BoundLogger = kwargs.get("log", LOGGER.new())
        log.debug("Get model by name", model_name=name, group_id=group_id)

        stmt = (
            select(models.MlModel)
            .join(models.Resource)
            .where(
                models.MlModel.name == name,
                models.Resource.group_id == group_id,
                models.Resource.is_deleted == False,  # noqa: E712
                models.Resource.latest_snapshot_id
                == models.MlModel.resource_snapshot_id,
            )
        )
        ml_model = db.session.scalars(stmt).first()

        if ml_model is None:
            if error_if_not_found:
                log.debug("Model not found", name=name)
                raise ModelDoesNotExistError

            return None

        return ml_model
