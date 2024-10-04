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
from typing import Any, ClassVar, Generic, Protocol, TypeVar

import structlog
from structlog.stdlib import BoundLogger

from .base import (
    CollectionClient,
    DioptraClientError,
    DioptraSession,
    SubCollectionClient,
    SubCollectionUrlError,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()

T = TypeVar("T")


class DraftFieldsValidationError(DioptraClientError):
    """Raised when one or more draft fields are invalid."""


class ValidateDraftFieldsProtocol(Protocol):
    def __call__(self, json_: dict[str, Any]) -> dict[str, Any]:
        ...  # fmt: skip


def make_draft_fields_validator(
    draft_fields: set[str], resource_name: str
) -> ValidateDraftFieldsProtocol:
    """Create a function to validate the allowed draft fields.

    Args:
        draft_fields: The allowed draft fields.
        resource_name: The name of the resource the draft fields are for.

    Returns:
        The function to validate the allowed draft fields.
    """

    def validate_draft_fields(json_: dict[str, Any]) -> dict[str, Any]:
        """Validate the provided draft fields.

        Args:
            json_: The draft fields to validate.

        Returns:
            The validated draft fields.

        Raises:
            DraftFieldsValidationError: If one or more draft fields are invalid or
                missing.
        """
        provided_fields = set(json_.keys())

        if draft_fields != provided_fields:
            invalid_fields = provided_fields - draft_fields
            missing_fields = draft_fields - provided_fields
            msg: list[str] = [f"Invalid or missing fields for {resource_name} draft."]

            if invalid_fields:
                msg.append(f"Invalid fields: {invalid_fields}")

            if missing_fields:
                msg.append(f"Missing fields: {missing_fields}")

            LOGGER.error(
                "Invalid or missing draft fields.",
                resource_name=resource_name,
                invalid_fields=invalid_fields,
                missing_fields=missing_fields,
            )
            raise DraftFieldsValidationError(" ".join(msg))

        return json_

    return validate_draft_fields


class NewResourceDraftsSubCollectionClient(Generic[T]):
    """The client for managing a new resource drafts sub-collection.

    Attributes:
        name: The name of the sub-collection managed by the client.
    """

    name: ClassVar[str] = "drafts"

    def __init__(
        self,
        session: DioptraSession[T],
        validate_fields_fn: ValidateDraftFieldsProtocol,
        root_collection: CollectionClient[T],
        parent_sub_collections: list[SubCollectionClient[T]] | None = None,
    ) -> None:
        """Initialize the NewResourceDraftsSubCollectionClient instance.

        Args:
            session: The Dioptra API session object.
            validate_fields_fn: The function to validate the allowed draft fields.
            root_collection: The client for the root collection that owns this
                sub-collection.
            parent_sub_collections: An ordered list of parent sub-collection clients
                that own this sub-collection and are also owned by the root collection.
                For example, a client for the hypothetical /col/{id1}/subColA/drafts
                collection would list the client for subColA as the parent
                sub-collection.
        """
        self._session = session
        self._validate_fields = validate_fields_fn
        self._root_collection = root_collection
        self._parent_sub_collections: list[SubCollectionClient[T]] = (
            parent_sub_collections or []
        )

    def get(
        self,
        *resource_ids: str | int,
        draft_type: str | None = None,
        group_id: int | None = None,
        index: int = 0,
        page_length: int = 10,
    ) -> T:
        """Get the list of endpoint drafts.

        Args:
            *resource_ids: The parent resource IDs that own the new resource drafts
                sub-collection.
            draft_type: The type of drafts to return: all, existing, or new.
            group_id: The group ID the drafts belong to. If None, return drafts from all
                groups that the user has access to.
            index: The paging index.
            page_length: The maximum number of drafts to return in the paged response.

        Returns:
            The response from the Dioptra API.
        """
        params: dict[str, Any] = {
            "index": index,
            "pageLength": page_length,
        }

        if group_id is not None:
            params["groupId"] = group_id

        if draft_type is not None:
            params["draftType"] = draft_type

        return self._session.get(
            self.build_sub_collection_url(*resource_ids), params=params
        )

    def get_by_id(self, *resource_ids: str | int, draft_id: int) -> T:
        """Get an endpoint draft by its ID.

        Args:
            *resource_ids: The parent resource IDs that own the new resource drafts
                sub-collection.
            draft_id: The ID of the draft.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(
            self.build_sub_collection_url(*resource_ids), str(draft_id)
        )

    def create(self, *resource_ids: str | int, group_id: int, **kwargs) -> T:
        """Create a new endpoint draft.

        Args:
            *resource_ids: The parent resource IDs that own the new resource drafts
                sub-collection.
            group_id: The ID for the group that will own the resource when the draft is
                published.
            **kwargs: The draft fields.

        Returns:
            The response from the Dioptra API.

        Raises:
            ValueError: If "group" is specified in kwargs.
        """

        if "group" in kwargs:
            raise ValueError('Cannot specify "group" in kwargs')

        data: dict[str, Any] = {"group": group_id} | self._validate_fields(kwargs)
        return self._session.post(
            self.build_sub_collection_url(*resource_ids), json_=data
        )

    def modify(self, *resource_ids: str | int, draft_id: int, **kwargs) -> T:
        """Modify the endpoint draft matching the provided ID.

        Args:
            *resource_ids: The parent resource IDs that own the new resource drafts
                sub-collection.
            draft_id: The draft ID.
            **kwargs: The draft fields to modify.

        Returns:
            The response from the Dioptra API.

        Raises:
            ValueError: If "draftId" is specified in kwargs.
        """
        if "draftId" in kwargs:
            raise ValueError('Cannot specify "draftId" in kwargs')

        return self._session.put(
            self.build_sub_collection_url(*resource_ids),
            str(draft_id),
            json_=self._validate_fields(kwargs),
        )

    def delete(self, *resource_ids: str | int, draft_id: int) -> T:
        """Delete the endpoint draft matching the provided ID.

        Args:
            *resource_ids: The parent resource IDs that own the new resource drafts
                sub-collection.
            draft_id: The draft ID.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(
            self.build_sub_collection_url(*resource_ids), str(draft_id)
        )

    def build_sub_collection_url(self, *resource_ids: str | int) -> str:
        """Build a sub-collection URL owned by one or more parent resources.

        Args:
            *resource_ids: The parent resource IDs that own the sub-collection.

        Returns:
            The joined sub-collection URL.

        Raises:
            SubCollectionUrlError: If the number of resource IDs does not match the
                expected count. For example, a client for the hypothetical
                /col/{id1}/subColA/{id2}/subColB/drafts sub-collection would expect 2
                resource IDs.
        """
        self._validate_resource_ids_count(*resource_ids)
        parent_url_parts: list[str] = [self._root_collection.url]

        for resource_id, parent_sub_collection in zip(
            resource_ids, self._parent_sub_collections
        ):
            parent_url_parts.extend([str(resource_id), parent_sub_collection.name])

        return self._session.build_url(*parent_url_parts, self.name)

    def _validate_resource_ids_count(self, *resource_ids: str | int) -> None:
        num_resource_ids = len(resource_ids)
        expected_count = len(self._parent_sub_collections)
        if num_resource_ids != expected_count:
            raise SubCollectionUrlError(
                f"Invalid number of resource ids (reason: expected {expected_count}): "
                f"{num_resource_ids}"
            )


class ExistingResourceDraftsSubCollectionClient(SubCollectionClient[T]):
    """The client for managing an existing resource drafts sub-collection.

    Attributes:
        name: The name of the sub-collection managed by the client.
    """

    name: ClassVar[str] = "draft"

    def __init__(
        self,
        session: DioptraSession[T],
        validate_fields_fn: ValidateDraftFieldsProtocol,
        root_collection: CollectionClient[T],
        parent_sub_collections: list[SubCollectionClient[T]] | None = None,
    ) -> None:
        """Initialize the ExistingResourceDraftsSubCollectionClient instance.

        Args:
            session: The Dioptra API session object.
            parent_endpoint: The parent endpoint client.
            validate_fields_fn: The function to validate the allowed draft fields.
        Args:
            session: The Dioptra API session object.
            validate_fields_fn: The function to validate the allowed draft fields.
            root_collection: The client for the root collection that owns this
                sub-collection.
            parent_sub_collections: An ordered list of parent sub-collection clients
                that own this sub-collection and are also owned by the root collection.
                For example, a client for the hypothetical
                /col/{id1}/subColA/{id2}/draft collection would list the client for
                subColA as the parent sub-collection.
        """
        super().__init__(
            session,
            root_collection=root_collection,
            parent_sub_collections=parent_sub_collections,
        )
        self._validate_fields = validate_fields_fn

    def get_by_id(self, *resource_ids: str | int) -> T:
        """Get the draft for a specific endpoint resource.

        Args:
            *resource_ids: The parent resource IDs that own the sub-collection.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.build_sub_collection_url(*resource_ids))

    def create(self, *resource_ids: str | int, **kwargs) -> T:
        """Create a draft for a specific endpoint resource.

        Args:
            *resource_ids: The parent resource IDs that own the sub-collection.
            **kwargs: The draft fields.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.post(
            self.build_sub_collection_url(*resource_ids),
            json_=self._validate_fields(kwargs),
        )

    def modify(self, *resource_ids: str | int, **kwargs) -> T:
        """Modify the draft for a specific endpoint resource.

        Args:
            *resource_ids: The parent resource IDs that own the sub-collection.
            **kwargs: The draft fields to modify.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.put(
            self.build_sub_collection_url(*resource_ids),
            json_=self._validate_fields(kwargs),
        )

    def delete(self, *resource_ids: str | int) -> T:
        """Delete the draft for a specific endpoint resource.

        Args:
            *resource_ids: The parent resource IDs that own the sub-collection.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(self.build_sub_collection_url(*resource_ids))
