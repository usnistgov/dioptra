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
import warnings
from typing import Any, ClassVar, Generic, Protocol, TypeVar, cast

from .base import (
    CollectionClient,
    DioptraClientError,
    DioptraSession,
    FieldsValidationError,
    SubCollectionClient,
    SubCollectionUrlError,
)

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
            reason: list[str] = []

            if invalid_fields:
                reason.append(f"{invalid_fields} are invalid")

            if missing_fields:
                reason.append(f"{missing_fields} are missing")

            raise DraftFieldsValidationError(
                "Invalid or missing fields for resource draft "
                f"(reason: {', '.join(reason)}): {resource_name}"
            )

        return json_

    return validate_draft_fields


class NewResourceDraftsSubCollectionClient(Generic[T]):
    """The client for managing a new resource drafts sub-collection.

    Attributes:
        name: The name of the sub-collection.
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
        """Get the list of new resource drafts.

        Args:
            *resource_ids: The parent resource ids that own the new resource drafts
                sub-collection.
            draft_type: The type of drafts to return: all, existing, or new. Optional,
                defaults to None.
            group_id: The group id the drafts belong to. If None, return drafts from all
                groups that the user has access to. Optional, defaults to None.
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of drafts to return in the paged response.
                Optional, defaults to 10.

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
        """Get a new resource draft by its id.

        Args:
            *resource_ids: The parent resource ids that own the new resource drafts
                sub-collection.
            draft_id: The draft id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(
            self.build_sub_collection_url(*resource_ids), str(draft_id)
        )

    def create(
        self, *resource_ids: str | int, group_id: int | None = None, **kwargs
    ) -> T:
        """Create a new resource draft.

        Args:
            *resource_ids: The parent resource ids that own the new resource drafts
                sub-collection.
            group_id: The id for the group that will own the resource when the draft is
                published.
            **kwargs: The draft fields.

        Returns:
            The response from the Dioptra API.

        Raises:
            FieldsValidationError: If "group" is specified in kwargs or if group_id is
                None and the client has no parent sub-collections.
            DraftFieldsValidationError: If one or more draft fields are invalid or
                missing.
        """

        if "group" in kwargs:
            raise FieldsValidationError(
                "Invalid argument (reason: keyword is reserved): group"
            )

        data: dict[str, Any] = (
            self._validate_group_id(group_id) | self._validate_fields(kwargs)
        )  # fmt: skip
        return self._session.post(
            self.build_sub_collection_url(*resource_ids), json_=data
        )

    def modify(self, *resource_ids: str | int, draft_id: int, **kwargs) -> T:
        """Modify the new resource draft matching the provided id.

        Args:
            *resource_ids: The parent resource ids that own the new resource drafts
                sub-collection.
            draft_id: The draft id, an integer.
            **kwargs: The draft fields to modify.

        Returns:
            The response from the Dioptra API.

        Raises:
            FieldsValidationError: If "draftId" is specified in kwargs.
            DraftFieldsValidationError: If one or more draft fields are invalid or
                missing.
        """
        if "draftId" in kwargs:
            raise FieldsValidationError(
                "Invalid argument (reason: keyword is reserved): draftId"
            )

        return self._session.put(
            self.build_sub_collection_url(*resource_ids),
            str(draft_id),
            json_=self._validate_fields(kwargs),
        )

    def delete(self, *resource_ids: str | int, draft_id: int) -> T:
        """Delete the new resource draft matching the provided id.

        Args:
            *resource_ids: The parent resource ids that own the new resource drafts
                sub-collection.
            draft_id: The draft id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(
            self.build_sub_collection_url(*resource_ids), str(draft_id)
        )

    def build_sub_collection_url(self, *resource_ids: str | int) -> str:
        """Build a sub-collection URL owned by one or more parent resources.

        Args:
            *resource_ids: The parent resource ids that own the sub-collection.

        Returns:
            The joined sub-collection URL.

        Raises:
            SubCollectionUrlError: If the number of resource ids does not match the
                expected count. For example, a client for the hypothetical
                /col/{id1}/subColA/{id2}/subColB/drafts sub-collection would expect 2
                resource ids.
        """
        self._validate_resource_ids_count(*resource_ids)
        parent_url_parts: list[str] = [self._root_collection.url]

        for resource_id, parent_sub_collection in zip(
            resource_ids, self._parent_sub_collections
        ):
            parent_url_parts.extend([str(resource_id), parent_sub_collection.name])

        return self._session.build_url(*parent_url_parts, self.name)

    def _validate_group_id(self, group_id: int | None) -> dict[str, Any]:
        if not self._parent_sub_collections:
            if group_id is None:
                raise FieldsValidationError(
                    "Invalid argument (reason: argument cannot be None): group_id"
                )

            return {"group": group_id}

        if group_id is not None:
            warnings.warn(
                '"group_id" argument ignored (reason: creating draft for '
                "sub-resource where group is known)",
                stacklevel=2,
            )

        return cast(dict[str, Any], {})

    def _validate_resource_ids_count(self, *resource_ids: str | int) -> None:
        num_resource_ids = len(resource_ids)
        expected_count = len(self._parent_sub_collections)
        if num_resource_ids != expected_count:
            raise SubCollectionUrlError(
                f"Invalid number of resource ids (reason: expected {expected_count}): "
                f"{num_resource_ids}"
            )


class ModifyResourceDraftsSubCollectionClient(SubCollectionClient[T]):
    """The client for managing a resource modification drafts sub-collection.

    Attributes:
        name: The name of the sub-collection.
    """

    name: ClassVar[str] = "draft"

    def __init__(
        self,
        session: DioptraSession[T],
        validate_fields_fn: ValidateDraftFieldsProtocol,
        root_collection: CollectionClient[T],
        parent_sub_collections: list[SubCollectionClient[T]] | None = None,
    ) -> None:
        """Initialize the ModifyResourceDraftsSubCollectionClient instance.

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
        """Get a resource modification draft.

        Args:
            *resource_ids: The parent resource ids that own the sub-collection.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.build_sub_collection_url(*resource_ids))

    def create(self, *resource_ids: str | int, **kwargs) -> T:
        """Create a resource modification draft.

        Args:
            *resource_ids: The parent resource ids that own the sub-collection.
            **kwargs: The draft fields.

        Returns:
            The response from the Dioptra API.

        Raises:
            DraftFieldsValidationError: If one or more draft fields are invalid or
                missing.
        """
        return self._session.post(
            self.build_sub_collection_url(*resource_ids),
            json_=self._validate_fields(kwargs),
        )

    def modify(self, *resource_ids: str | int, **kwargs) -> T:
        """Modify a resource modification draft.

        Args:
            *resource_ids: The parent resource ids that own the sub-collection.
            **kwargs: The draft fields to modify.

        Returns:
            The response from the Dioptra API.

        Raises:
            DraftFieldsValidationError: If one or more draft fields are invalid or
                missing.
        """
        return self._session.put(
            self.build_sub_collection_url(*resource_ids),
            json_=self._validate_fields(kwargs),
        )

    def delete(self, *resource_ids: str | int) -> T:
        """Delete a resource modification draft.

        Args:
            *resource_ids: The parent resource ids that own the sub-collection.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(self.build_sub_collection_url(*resource_ids))
