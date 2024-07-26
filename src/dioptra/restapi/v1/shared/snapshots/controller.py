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
"""The module defining the endpoints for Snapshots."""
import uuid
from typing import Any, Callable, Type, cast
from urllib.parse import unquote

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import ClassAssistedBuilder, inject
from marshmallow import Schema
from structlog.stdlib import BoundLogger

from dioptra.restapi.db import models
from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.schemas import ResourceGetQueryParameters

from .service import ResourceSnapshotsIdService, ResourceSnapshotsService

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def generate_resource_snapshots_endpoint(
    api: Namespace,
    resource_model: Type[models.ResourceSnapshot],
    resource_name: str,
    route_prefix: str,
    searchable_fields: dict[str, Any],
    page_schema: Type[Schema],
    build_fn: Callable,
) -> Resource:
    """Generates a ResourceSnapshotsEndpoint class.

    Args:
        api: The API
        resource_model: The ORM class for the resource snapshot.
        resource_name: The name of the resource.
        route_prefix: The prefix to append to the API URL.
        searchable_fields: A dictionary where the keys are the fields that can be
            searched and the values control how the query is constructed in the where
            clause.
        page_schema: The Marshmallow schema for the page response.
        build_fn: A function that builds the response object.

    Returns:
        The parameterized ResourceSnapshotsEndpoint class.
    """

    # Based on: https://github.com/apryor6/flask_accepts/blob/05567461c421a534d6fc6e122d5e086b0b0e53aa/flask_accepts/utils.py#L154-L160  # noqa: B950
    if isinstance(page_schema, Schema):
        model_name = "Snapshots" + "".join(
            page_schema.__class__.__name__.rsplit("Schema", 1)
        )
    else:
        model_name = "Snapshots" + "".join(page_schema.__name__.rsplit("Schema", 1))

    @api.route("/<int:id>/snapshots")
    @api.param("id", f"ID for the {resource_name} resource.")
    class ResourceSnapshotsEndpoint(Resource):
        @inject
        def __init__(
            self,
            snapshots_service: ClassAssistedBuilder[ResourceSnapshotsService],
            *args,
            **kwargs,
        ) -> None:
            self._snapshots_service = snapshots_service.build(
                resource_model=resource_model,
                resource_type=resource_name,
                searchable_fields=searchable_fields,
            )
            super().__init__(*args, **kwargs)

        @login_required
        @accepts(query_params_schema=ResourceGetQueryParameters, api=api)
        @responds(schema=page_schema, model_name=model_name, api=api)
        def get(self, id: int):
            """Gets the Snapshots for the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Snapshots", request_type="GET"
            )

            parsed_query_params = request.parsed_query_params  # type: ignore
            search_string = unquote(parsed_query_params["search"])
            page_index = parsed_query_params["index"]
            page_length = parsed_query_params["page_length"]

            snapshots, total_num_snapshots = cast(
                tuple[list[dict[str, Any]], int],
                self._snapshots_service.get(
                    resource_id=id,
                    search_string=search_string,
                    page_index=page_index,
                    page_length=page_length,
                    error_if_not_found=True,
                    log=log,
                ),
            )
            return utils.build_paging_envelope(
                f"{route_prefix}/{id}/snapshots",
                build_fn=build_fn,
                data=snapshots,
                group_id=None,
                query=search_string,
                draft_type=None,
                index=page_index,
                length=page_length,
                total_num_elements=total_num_snapshots,
            )

    return ResourceSnapshotsEndpoint


def generate_resource_snapshots_id_endpoint(
    api: Namespace,
    resource_model: Type[models.ResourceSnapshot],
    resource_name: str,
    response_schema: Type[Schema],
    build_fn: Callable,
) -> Resource:
    """Generates a ResourceSnapshotsIdEndpoint class.

    Args:
        api: The API
        resource_model: The ORM class for the resource snapshot.
        resource_name: The name of the resource.
        response_schema: The Marshmallow schema for the response.
        build_fn: A function that builds the response object.

    Returns:
        The parameterized ResourceSnapshotsIdEndpoint class.
    """

    # Based on: https://github.com/apryor6/flask_accepts/blob/05567461c421a534d6fc6e122d5e086b0b0e53aa/flask_accepts/utils.py#L154-L160  # noqa: B950
    if isinstance(response_schema, Schema):
        model_name = "SnapshotsId" + "".join(
            response_schema.__class__.__name__.rsplit("Schema", 1)
        )
    else:
        model_name = "SnapshotsId" + "".join(
            response_schema.__name__.rsplit("Schema", 1)
        )

    @api.route("/<int:id>/snapshots/<int:snapshotId>")
    @api.param("id", f"ID for the {resource_name} resource.")
    @api.param("snapshotId", f"Snapshot ID for the {resource_name} resource.")
    class ResourcesSnapshotsIdEndpoint(Resource):
        @inject
        def __init__(
            self,
            snapshots_id_service: ClassAssistedBuilder[ResourceSnapshotsIdService],
            *args,
            **kwargs,
        ) -> None:
            self._snapshots_id_service = snapshots_id_service.build(
                resource_model=resource_model,
                resource_type=resource_name,
            )
            super().__init__(*args, **kwargs)

        @login_required
        @responds(schema=response_schema, model_name=model_name, api=api)
        def get(self, id: int, snapshotId: int):
            """Gets a Snapshot for the resource by snapshot id."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Snapshots", request_type="GET"
            )
            snapshot = cast(
                models.ResourceSnapshot,
                self._snapshots_id_service.get(
                    id, snapshot_id=snapshotId, error_if_not_found=True, log=log
                ),
            )
            return build_fn(snapshot)

    return ResourcesSnapshotsIdEndpoint


def generate_nested_resource_snapshots_endpoint(
    api: Namespace,
    resource_model: Type[models.ResourceSnapshot],
    resource_name: str,
    resource_route: str,
    base_resource_route: str,
    searchable_fields: dict[str, Any],
    page_schema: Type[Schema],
    build_fn: Callable,
) -> Resource:
    """Generates a ResourceSnapshotsEndpoint class.

    Args:
        api: The API
        resource_model: The ORM class for the resource snapshot.
        resource_name: The name of the resource.
        route_prefix: The prefix to append to the API URL.
        searchable_fields: A dictionary where the keys are the fields that can be
            searched and the values control how the query is constructed in the where
            clause.
        page_schema: The Marshmallow schema for the page response.
        build_fn: A function that builds the response object.

    Returns:
        The parameterized ResourceSnapshotsEndpoint class.
    """

    # Based on: https://github.com/apryor6/flask_accepts/blob/05567461c421a534d6fc6e122d5e086b0b0e53aa/flask_accepts/utils.py#L154-L160  # noqa: B950
    if isinstance(page_schema, Schema):
        model_name = "NestedSnapshots" + "".join(
            page_schema.__class__.__name__.rsplit("Schema", 1)
        )
    else:
        model_name = "NestedSnapshots" + "".join(
            page_schema.__name__.rsplit("Schema", 1)
        )

    route_singular = resource_route[:-1]
    resource_id = f"{route_singular}Id"

    @api.route(f"/<int:id>/{resource_route}/<int:{resource_id}>/snapshots")
    @api.param("id", f"ID for the {resource_name}.")
    @api.param(f"{resource_id}", f"ID for the {resource_name}.")
    class ResourceSnapshotsEndpoint(Resource):
        @inject
        def __init__(
            self,
            snapshots_service: ClassAssistedBuilder[ResourceSnapshotsService],
            *args,
            **kwargs,
        ) -> None:
            self._snapshots_service = snapshots_service.build(
                resource_model=resource_model,
                resource_type=resource_name,
                searchable_fields=searchable_fields,
            )
            super().__init__(*args, **kwargs)

        @login_required
        @accepts(query_params_schema=ResourceGetQueryParameters, api=api)
        @responds(schema=page_schema, model_name=model_name, api=api)
        def get(self, id: int, **kwargs):
            """Gets the Snapshots for the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Snapshots", request_type="GET"
            )
            if set(kwargs.keys()) != set([resource_id]):
                unexpected_kwargs = {
                    k: v for k, v in kwargs.items() if resource_id != k
                }
                log.error("Unexpected input", kwargs=unexpected_kwargs)
                raise TypeError(
                    "delete method received unexpected keyword arguments: "
                    f"{list(unexpected_kwargs.keys())}"
                )

            parsed_query_params = request.parsed_query_params  # type: ignore
            search_string = unquote(parsed_query_params["search"])
            page_index = parsed_query_params["index"]
            page_length = parsed_query_params["page_length"]

            snapshots, total_num_snapshots = cast(
                tuple[list[models.ResourceSnapshot], int],
                self._snapshots_service.get(
                    resource_id=kwargs[resource_id],
                    search_string=search_string,
                    page_index=page_index,
                    page_length=page_length,
                    error_if_not_found=True,
                    log=log,
                ),
            )
            return utils.build_paging_envelope(
                f"{base_resource_route}/{id}/"
                f"{resource_route}/{kwargs[resource_id]}/snapshots",
                build_fn=build_fn,
                data=snapshots,
                group_id=None,
                query=search_string,
                draft_type=None,
                index=page_index,
                length=page_length,
                total_num_elements=total_num_snapshots,
            )

    return ResourceSnapshotsEndpoint


def generate_nested_resource_snapshots_id_endpoint(
    api: Namespace,
    resource_model: Type[models.ResourceSnapshot],
    resource_name: str,
    resource_route: str,
    response_schema: Type[Schema],
    build_fn: Callable,
) -> Resource:
    """Generates a ResourceSnapshotsIdEndpoint class.

    Args:
        api: The API
        resource_model: The ORM class for the resource snapshot.
        resource_name: The name of the resource.
        response_schema: The Marshmallow schema for the response.
        build_fn: A function that builds the response object.

    Returns:
        The parameterized ResourceSnapshotsIdEndpoint class.
    """

    route_singular = resource_route[:-1]
    resource_id = f"{route_singular}Id"

    # Based on: https://github.com/apryor6/flask_accepts/blob/05567461c421a534d6fc6e122d5e086b0b0e53aa/flask_accepts/utils.py#L154-L160  # noqa: B950
    if isinstance(response_schema, Schema):
        model_name = "NestedSnapshotsId" + "".join(
            response_schema.__class__.__name__.rsplit("Schema", 1)
        )
    else:
        model_name = "NestedSnapshotsId" + "".join(
            response_schema.__name__.rsplit("Schema", 1)
        )

    @api.route(
        f"/<int:id>/{resource_route}/<int:{resource_id}>/snapshots/<int:snapshotId>"
    )
    @api.param("id", f"ID for the {resource_name}.")
    @api.param(f"{resource_id}", f"ID for the {resource_name}.")
    @api.param("snapshotId", "ID for the Snapshot.")
    class ResourcesSnapshotsIdEndpoint(Resource):
        @inject
        def __init__(
            self,
            snapshots_id_service: ClassAssistedBuilder[ResourceSnapshotsIdService],
            *args,
            **kwargs,
        ) -> None:
            self._snapshots_id_service = snapshots_id_service.build(
                resource_model=resource_model,
                resource_type=resource_name,
            )
            super().__init__(*args, **kwargs)

        @login_required
        @responds(schema=response_schema, model_name=model_name, api=api)
        def get(self, id: int, snapshotId: int, **kwargs):
            """Gets a Snapshot for the resource by snapshot id."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Snapshots", request_type="GET"
            )
            if set(kwargs.keys()) != set([resource_id]):
                unexpected_kwargs = {
                    k: v for k, v in kwargs.items() if resource_id != k
                }
                log.error("Unexpected input", kwargs=unexpected_kwargs)
                raise TypeError(
                    "delete method received unexpected keyword arguments: "
                    f"{list(unexpected_kwargs.keys())}"
                )

            snapshot = cast(
                models.ResourceSnapshot,
                self._snapshots_id_service.get(
                    kwargs[resource_id],
                    snapshot_id=snapshotId,
                    error_if_not_found=True,
                    log=log,
                ),
            )
            return build_fn(snapshot)

    return ResourcesSnapshotsIdEndpoint
