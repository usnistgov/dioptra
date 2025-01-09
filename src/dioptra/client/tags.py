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
from typing import Any, ClassVar, TypeVar

from .base import CollectionClient, SubCollectionClient

T = TypeVar("T")


class TagsCollectionClient(CollectionClient[T]):
    """The client for interacting with the Dioptra API's /tags collection.

    Attributes:
        name: The name of the collection.
    """

    name: ClassVar[str] = "tags"

    def get(
        self,
        group_id: int | None = None,
        index: int = 0,
        page_length: int = 10,
        sort_by: str | None = None,
        descending: bool | None = None,
        search: str | None = None,
    ) -> T:
        """Get a list of tags.

        Args:
            group_id: The group id the tags belong to. If None, return tags from all
                groups that the user has access to. Optional, defaults to None.
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of tags to return in the paged response.
                Optional, defaults to 10.
            sort_by: The field to use to sort the returned list. Optional, defaults to
                None.
            descending: Sort the returned list in descending order. Optional, defaults
                to None.
            search: Search for tags using the Dioptra API's query language. Optional,
                defaults to None.

        Returns:
            The response from the Dioptra API.
        """
        params: dict[str, Any] = {
            "index": index,
            "pageLength": page_length,
        }

        if sort_by is not None:
            params["sortBy"] = sort_by

        if descending is not None:
            params["descending"] = descending

        if search is not None:
            params["search"] = search

        if group_id is not None:
            params["groupId"] = group_id

        return self._session.get(
            self.url,
            params=params,
        )

    def get_by_id(self, tag_id: str | int) -> T:
        """Get the tag matching the provided id.

        Args:
            tag_id: The tag id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(tag_id))

    def create(self, group_id: int, name: str) -> T:
        """Creates a tag.

        Args:
            group_id: The id of the group that will own the tag.
            name: The name of the new tag.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {
            "group": group_id,
            "name": name,
        }

        return self._session.post(self.url, json_=json_)

    def modify_by_id(self, tag_id: str | int, name: str) -> T:
        """Modify the tag matching the provided id.

        Args:
            tag_id: The tag id, an integer.
            name: The new name of the tag.

        Returns:
            The response from the Dioptra API.
        """
        json_ = {"name": name}

        return self._session.put(self.url, str(tag_id), json_=json_)

    def delete_by_id(self, tag_id: str | int) -> T:
        """Delete the tag matching the provided id.

        Args:
            tag_id: The tag id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(self.url, str(tag_id))

    def get_resources_for_tag(
        self,
        tag_id: str | int,
        resource_type: str | None = None,
        index: int = 0,
        page_length: int = 10,
    ) -> T:
        """Get a list of resources labeled with a tag.

        Args:
            tag_id: The tag id, an integer.
            resource_type: The type of resource to filter by. If None, return all
                resources associated with the tag. Optional, defaults to None.
            index: The paging index.
            page_length: The maximum number of tags to return in the paged response.

        Returns:
            The response from the Dioptra API.
        """
        params: dict[str, Any] = {
            "index": index,
            "pageLength": page_length,
        }

        if resource_type is not None:
            params["resourceType"] = resource_type

        return self._session.get(
            self.url,
            str(tag_id),
            "resources",
            params=params,
        )


class TagsSubCollectionClient(SubCollectionClient[T]):
    """The client for managing a tags sub-collection.

    Attributes:
        name: The name of the sub-collection.
    """

    name: ClassVar[str] = "tags"

    def get(self, *resource_ids: str | int) -> T:
        """Get a list of tags.

        Args:
            *resource_ids: The parent resource ids that own the tags sub-collection.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.build_sub_collection_url(*resource_ids))

    def modify(
        self,
        *resource_ids: str | int,
        ids: list[int],
    ) -> T:
        """Change the list of tags associated with an endpoint resource.

        This method overwrites the existing list of tags associated with an endpoint
        resource. To non-destructively append multiple tags, use the `append` method. To
        delete an individual tag, use the `remove` method.

        Args:
            *resource_ids: The parent resource ids that own the tags sub-collection.
            ids: The list of tag ids to set on the resource.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.put(
            self.build_sub_collection_url(*resource_ids),
            json_={"ids": ids},
        )

    def append(
        self,
        *resource_ids: str | int,
        ids: list[int],
    ) -> T:
        """Append one or more tags to an endpoint resource.

        Tag ids that have already been appended to the endpoint resource will be
        ignored.

        Args:
            *resource_ids: The parent resource ids that own the tags sub-collection.
            ids: The list of tag ids to append to the endpoint resource.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.post(
            self.build_sub_collection_url(*resource_ids),
            json_={"ids": ids},
        )

    def remove(
        self,
        *resource_ids: str | int,
        tag_id: int,
    ) -> T:
        """Remove a tag from an endpoint resource.

        Args:
            *resource_ids: The parent resource ids that own the tags sub-collection.
            tag_id: The id of the tag to remove from the endpoint resource.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(
            self.build_sub_collection_url(*resource_ids), str(tag_id)
        )

    def remove_all(
        self,
        *resource_ids: str | int,
    ) -> T:
        """Remove all tags from an endpoint resource.

        This method will remove all tags from the endpoint resource and cannot be
        reversed. To remove individual tags, use the `remove` method.

        Args:
            *resource_ids: The parent resource ids that own the tags sub-collection.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(self.build_sub_collection_url(*resource_ids))
