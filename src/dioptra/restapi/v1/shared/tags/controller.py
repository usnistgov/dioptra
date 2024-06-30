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
"""The module defining the endpoints for Tags."""
from __future__ import annotations

import uuid

import structlog
from flask import request
from flask_accepts import accepts, responds
from flask_login import login_required
from flask_restx import Namespace, Resource
from injector import ClassAssistedBuilder, inject
from structlog.stdlib import BoundLogger

from dioptra.restapi.v1 import utils
from dioptra.restapi.v1.schemas import IdListSchema, IdStatusResponseSchema
from dioptra.restapi.v1.tags.schema import TagRefSchema

from .service import ResourceTagsIdService, ResourceTagsService

LOGGER: BoundLogger = structlog.stdlib.get_logger()

api: Namespace = Namespace("Tags", description="Tags sub-endpoint")


def generate_resource_tags_endpoint(
    api: Namespace,
    resource_name: str,
) -> Resource:
    """
    Generates an Endpoint for managing Tags on Resources

    Args:
        api: The API namespace
        resource_name: The name of the resource

    Returns:
        The generated Endpoint class
    """

    @api.route("/<int:id>/tags")
    @api.param("id", f"ID for the {resource_name}.")
    class ResourcesTagsEndpoint(Resource):
        @inject
        def __init__(
            self,
            tag_service: ClassAssistedBuilder[ResourceTagsService],
            *args,
            **kwargs,
        ) -> None:
            self._tag_service = tag_service.build(resource_type=resource_name)
            super().__init__(*args, **kwargs)

        @login_required
        @responds(schema=TagRefSchema(many=True), api=api)
        def get(self, id: int):
            """Gets the list of Tags for the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Tag", request_type="GET"
            )
            tags = self._tag_service.get(id, log=log)
            return utils.build_tag_ref_list(tags)

        @login_required
        @accepts(schema=IdListSchema, api=api)
        @responds(schema=TagRefSchema(many=True), api=api)
        def post(self, id: int):
            """Appends one or more Tags to the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Tag", request_type="POST"
            )
            parsed_obj = request.parsed_obj  # type: ignore
            tags = self._tag_service.append(
                id, tag_ids=parsed_obj["ids"], error_if_not_found=True, log=log
            )
            return utils.build_tag_ref_list(tags)

        @login_required
        @accepts(schema=IdListSchema, api=api)
        @responds(schema=TagRefSchema(many=True), api=api)
        def put(self, id: int):
            """Replaces one or more Tags to the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Tag", request_type="POST"
            )
            parsed_obj = request.parsed_obj  # type: ignore
            tags = self._tag_service.modify(
                id, tag_ids=parsed_obj["ids"], error_if_not_found=True, log=log
            )
            return utils.build_tag_ref_list(tags)

        @login_required
        @responds(schema=IdStatusResponseSchema, api=api)
        def delete(self, id: int):
            """Removes all Tags from the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Tag", request_type="DELETE"
            )
            return self._tag_service.delete(id, error_if_not_found=True, log=log)

    return ResourcesTagsEndpoint


def generate_resource_tags_id_endpoint(
    api: Namespace,
    resource_name: str,
) -> Resource:
    """
    Generates an Endpoint for removing a Tag from a Resource.

    Args:
        api: The API namespace
        resource_name: The name of the resource

    Returns:
        The generated Endpoint class
    """

    @api.route("/<int:id>/tags/<int:tagId>")
    @api.param("id", f"ID for the {resource_name}.")
    @api.param("tagId", "ID for the Tag.")
    class ResourcesTagsIdEndpoint(Resource):
        @inject
        def __init__(
            self,
            tag_id_service: ClassAssistedBuilder[ResourceTagsIdService],
            *args,
            **kwargs,
        ) -> None:
            self._tag_id_service = tag_id_service.build(resource_type=resource_name)
            super().__init__(*args, **kwargs)

        @login_required
        @responds(schema=IdStatusResponseSchema, api=api)
        def delete(self, id: int, tagId: int):
            """Removes a Tag from the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Tag", request_type="GET"
            )
            return self._tag_id_service.delete(id, tagId, log=log)

    return ResourcesTagsIdEndpoint


def generate_nested_resource_tags_endpoint(
    api: Namespace,
    resource_name: str,
    resource_route: str,
    base_resource_name: str,
) -> Resource:
    """
    Generates an Endpoint for managing Tags on Resources

    Args:
        api: The API namespace
        resource_name: The name of the nested resource
        resource_route: The route to the nested resource
        base_resource_name: The name of the resource

    Returns:
        The generated Endpoint class
    """

    route_singular = resource_route[:-1]
    resource_id = f"{route_singular}Id"

    @api.route(f"/<int:id>/{resource_route}/<int:{resource_id}>/tags/")
    @api.param("id", f"ID for the {base_resource_name}.")
    @api.param(f"{resource_id}", f"ID for the {resource_name}.")
    class ResourcesTagsEndpoint(Resource):
        @inject
        def __init__(
            self,
            tag_service: ClassAssistedBuilder[ResourceTagsService],
            *args,
            **kwargs,
        ) -> None:
            self._tag_service = tag_service.build(resource_type=resource_name)
            super().__init__(*args, **kwargs)

        @login_required
        @responds(schema=TagRefSchema(many=True), api=api)
        def get(self, id: int, **kwargs):
            """Gets the list of Tags for the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Tag", request_type="GET"
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

            tags = self._tag_service.get(kwargs[resource_id], log=log)
            return utils.build_tag_ref_list(tags)

        @login_required
        @accepts(schema=IdListSchema, api=api)
        @responds(schema=TagRefSchema(many=True), api=api)
        def post(self, id: int, **kwargs):
            """Appends one or more Tags to the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Tag", request_type="POST"
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

            parsed_obj = request.parsed_obj  # type: ignore
            tags = self._tag_service.append(
                kwargs[resource_id],
                tag_ids=parsed_obj["ids"],
                error_if_not_found=True,
                log=log,
            )
            return utils.build_tag_ref_list(tags)

        @login_required
        @accepts(schema=IdListSchema, api=api)
        @responds(schema=TagRefSchema(many=True), api=api)
        def put(self, id: int, **kwargs):
            """Replaces one or more Tags to the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Tag", request_type="POST"
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

            parsed_obj = request.parsed_obj  # type: ignore
            tags = self._tag_service.modify(
                kwargs[resource_id],
                tag_ids=parsed_obj["ids"],
                error_if_not_found=True,
                log=log,
            )
            return utils.build_tag_ref_list(tags)

        @login_required
        @responds(schema=IdStatusResponseSchema, api=api)
        def delete(self, id: int, **kwargs):
            """Removes all Tags from the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Tag", request_type="DELETE"
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

            return self._tag_service.delete(
                kwargs[resource_id], error_if_not_found=True, log=log
            )

    return ResourcesTagsEndpoint


def generate_nested_resource_tags_id_endpoint(
    api: Namespace,
    resource_name: str,
    resource_route: str,
    base_resource_name: str,
) -> Resource:
    """
    Generates an Endpoint for removing a Tag from a Resource.

    Args:
        api: The API namespace
        base_resource_name: The name of the resource
        resource_name: The name of the nested resource
        resource_route: The route to the nested resource

    Returns:
        The generated Endpoint class
    """

    route_singular = resource_route[:-1]
    resource_id = f"{route_singular}Id"

    @api.route(f"/<int:id>/{resource_route}/<int:{resource_id}>/tags/<int:tagId>")
    @api.param("id", f"ID for the {base_resource_name}.")
    @api.param(f"{resource_id}", f"ID for the {resource_name}.")
    @api.param("tagId", "ID for the Tag.")
    class ResourcesTagsIdEndpoint(Resource):
        @inject
        def __init__(
            self,
            tag_id_service: ClassAssistedBuilder[ResourceTagsIdService],
            *args,
            **kwargs,
        ) -> None:
            self._tag_id_service = tag_id_service.build(resource_type=resource_name)
            super().__init__(*args, **kwargs)

        @login_required
        @responds(schema=IdStatusResponseSchema, api=api)
        def delete(self, id: int, tagId: int, **kwargs):
            """Removes a Tag from the resource."""
            log = LOGGER.new(
                request_id=str(uuid.uuid4()), resource="Tag", request_type="DELETE"
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

            return self._tag_id_service.delete(kwargs[resource_id], tagId, log=log)

    return ResourcesTagsIdEndpoint
