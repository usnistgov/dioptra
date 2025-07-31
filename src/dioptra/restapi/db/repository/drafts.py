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
"""
The drafts repository: data operations related to drafts
"""

import datetime
import enum
from collections.abc import Iterable, Sequence
from typing import Any

import sqlalchemy as sa

from dioptra.restapi.db.models import (
    DraftResource,
    Group,
    Resource,
    ResourceSnapshot,
    User,
    resource_dependency_types_table,
)
from dioptra.restapi.db.repository.utils import (
    CompatibleSession,
    DeletionPolicy,
    S,
    assert_draft_does_not_exist,
    assert_draft_exists,
    assert_group_exists,
    assert_resource_exists,
    assert_snapshot_exists,
    assert_user_exists,
    assert_user_in_group,
    draft_exists,
    get_draft_id,
    get_group_id,
    get_resource_id,
    get_resource_snapshot_id,
    get_user_id,
)
from dioptra.restapi.errors import (
    DraftAlreadyExistsError,
    DraftBaseInvalidError,
    DraftDoesNotExistError,
    DraftModificationRequiredError,
    DraftSnapshotIdInvalidError,
    DraftTargetOwnerMismatch,
    EntityDeletedError,
    EntityDoesNotExistError,
)
from dioptra.restapi.v1.entity_types import EntityTypes


class DraftType(enum.Enum):
    ANY = enum.auto()  # Any draft
    RESOURCE = enum.auto()  # Draft resources only
    MODIFICATION = enum.auto()  # Draft modifications of existing resources only


class DraftsRepository:
    def __init__(self, session: CompatibleSession[S]) -> None:
        self._session = session

    def create_draft_resource(
        self,
        draft: DraftResource,
    ) -> None:
        """
        Create a draft resource.

        Args:
            draft: A DraftResource object containing a draft resource

        Raises:
            DraftAlreadyExistsError: if the draft already exists
            EntityDoesNotExistError: if the draft creator or target owner does
                not exist, or if the payload's base_resource_id refers to a
                resource which does not exist
            EntityDeletedError: if the draft creator or target owner is deleted,
                or if the payload's base_resource_id refers to a deleted
                resource
            UserNotInGroupError: if the draft creator user is not a member of
                the draft target owner group
            DraftBaseInvalidError: if the payload's base_resource_id refers
                to a resource of a type which is not legal to be a parent
                of the draft's resource type
        """
        assert_draft_does_not_exist(self._session, draft)
        assert_group_exists(
            self._session, draft.target_owner, DeletionPolicy.NOT_DELETED
        )
        assert_user_exists(self._session, draft.creator, DeletionPolicy.NOT_DELETED)
        assert_user_in_group(self._session, draft.creator, draft.target_owner)

        base_resource_id = draft.payload["base_resource_id"]
        if base_resource_id is not None:
            # trying to kill two birds with one stone here: check for base
            # resource existence/deletion, and check for legal base/draft
            # resource types.
            types_stmt = (
                sa.select(
                    Resource.is_deleted,
                    Resource.resource_type,
                    resource_dependency_types_table.c.child_resource_type,
                )
                .select_from(Resource)
                .where(
                    Resource.resource_id == base_resource_id,
                )
                .outerjoin(
                    resource_dependency_types_table,
                    sa.and_(
                        Resource.resource_type
                        == resource_dependency_types_table.c.parent_resource_type,
                        resource_dependency_types_table.c.child_resource_type
                        == draft.resource_type,
                    ),
                )
            )

            result = self._session.execute(types_stmt).first()

            if result:
                is_deleted, parent_resource_type, child_resource_type = result
                if is_deleted:
                    raise EntityDeletedError(
                        EntityTypes.get_from_string(parent_resource_type),
                        base_resource_id,
                    )

                if not child_resource_type:
                    raise DraftBaseInvalidError(
                        base_resource_id,
                        parent_resource_type,
                        draft.resource_type,
                    )
            else:
                raise EntityDoesNotExistError(
                    EntityTypes.NONE,
                    resource_id=base_resource_id,
                )

        # TODO: verify that the draft payload is for a draft resource, not a
        # draft modification?  Any other sanity checks necessary?

        self._session.add(draft)

    def create_draft_modification(
        self,
        draft: DraftResource,
    ):
        """
        Create a draft modification of an existing resource.

        Args:
            draft: A DraftResource object containing a draft modification of
                a resource

        Raises:
            DraftAlreadyExistsError: if the given draft already exists, or if
                the creator user already has an open draft modification for the
                same resource
            EntityDoesNotExistError: if the draft creator or target owner does
                not exist, or the payload's resource_id refers to a resource
                which does not exist, or the payload's resource_snapshot_id
                refers to a snapshot which does not exist
            EntityDeletedError: if the draft creator or target owner is
                deleted, or the payload's resource_id refers to a deleted
                resource
            UserNotInGroupError: if the draft creator user is not a member of
                the draft target owner group
            DraftSnapshotIdInvalidError: if the payload's resource_snapshot_id
                refers to a snapshot of a different resource than that referred
                to by the payload's resource_id
            DraftTargetOwnerMismatch: if the resource being modified has a
                different owner than the draft's target owner
        """

        assert_draft_does_not_exist(self._session, draft)
        assert_group_exists(
            self._session, draft.target_owner, DeletionPolicy.NOT_DELETED
        )
        assert_user_exists(self._session, draft.creator, DeletionPolicy.NOT_DELETED)
        assert_user_in_group(self._session, draft.creator, draft.target_owner)

        resource_id = draft.payload["resource_id"]
        resource_snapshot_id = draft.payload["resource_snapshot_id"]

        resource_obj = self.get_resource(resource_id, DeletionPolicy.ANY)
        if not resource_obj:
            raise EntityDoesNotExistError(EntityTypes.NONE, resource_id=resource_id)
        elif resource_obj.is_deleted:
            raise EntityDeletedError(
                EntityTypes.NONE, resource_id, resource_id=resource_id
            )

        assert_snapshot_exists(self._session, resource_snapshot_id)

        # Ensure the snapshot given is a snapshot of the resource given.
        _assert_snapshot_and_resource_id_match(
            self._session, resource_id, resource_snapshot_id
        )

        # These objects are constructed with an object owner, which does not
        # automatically set the foreign key attributes.  So, need the fallback
        # behavior to go through the relationship attributes.
        target_owner_id = draft.group_id or draft.target_owner.group_id
        resource_owner_id = resource_obj.group_id or resource_obj.owner.group_id
        if target_owner_id != resource_owner_id:
            # The draft modification and the resource being modified are not
            # owned by the same group.
            raise DraftTargetOwnerMismatch(
                target_owner_id,
                resource_owner_id,
            )

        # I guess a user may not have more than one draft modification per
        # resource?
        if self.has_draft_modification(resource_obj, draft.creator):
            raise DraftAlreadyExistsError(
                resource_obj.resource_type, resource_obj.resource_id
            )

        # TODO: verify that the draft payload is for a draft modification, not
        # a draft resource?  Any other sanity checks necessary?

        self._session.add(draft)

    def get(
        self,
        draft_id: int,
        resource_type: str | None = None,
        creator: User | int | None = None,
    ) -> DraftResource | None:
        """
        Get a draft (either kind) by ID.

        Args:
            draft_id: The ID of a draft
            resource_type: A resource type, used to pretend an existing draft
                doesn't exist if it's for the wrong type of resource; None to
                not filter by resource type
            creator: A User object or user_id integer primary key value, used
                to pretend an existing draft doesn't exist if it was created
                by the wrong user; None to not filter by user creator

        Returns:
            A DraftResource object, or None if one was not found according to
                the given criteria

        Raises:
            EntityDoesNotExistError: if a creator user is given but it does not
                exist
            EntityDeletedError:  if a creator user is given but it is deleted
        """

        if creator is not None:
            assert_user_exists(
                self._session,
                creator,
                DeletionPolicy.NOT_DELETED,
            )

        stmt = sa.select(DraftResource).where(
            DraftResource.draft_resource_id == draft_id
        )

        if resource_type is not None:
            stmt = stmt.where(DraftResource.resource_type == resource_type)

        if creator is not None:
            creator_id = get_user_id(creator)
            if creator_id is not None:
                stmt = stmt.where(DraftResource.user_id == creator_id)

        draft = self._session.scalar(stmt)

        return draft

    def get_one(
        self,
        draft_id: int,
        resource_type: str | None = None,
        creator: User | int | None = None,
    ) -> DraftResource:
        """
        Get a draft (either kind) by ID.  Analogous to .get(), but raises
        an exception instead of returning None.

        Args:
            draft_id: The ID of a draft
            resource_type: A resource type, used to pretend an existing draft
                doesn't exist if it's for the wrong type of resource; None to
                not filter by resource type
            creator: A User object or user_id integer primary key value, used
                to pretend an existing draft doesn't exist if it was created
                by the wrong user; None to not filter by user creator

        Returns:
            A DraftResource object

        Raises:
            EntityDoesNotExistError: if a creator user is given but it does not
                exist
            EntityDeletedError: if a creator user is given but it is deleted
            DraftDoesNotExistError: if the draft is not found
        """

        draft = self.get(draft_id, resource_type, creator)
        if not draft:
            raise DraftDoesNotExistError(draft_resource_id=draft_id)

        return draft

    def get_resource(
        self,
        resource_id: int,
        deletion_policy: DeletionPolicy = DeletionPolicy.NOT_DELETED,
    ) -> Resource | None:
        """
        Look up a resource by ID.

        Args:
            resource_id: A resource ID
            deletion_policy: Whether to look at deleted resources, non-deleted
                resources, or all resources

        Returns:
            A Resource object, or None if one was not found
        """

        stmt = sa.select(Resource).where(Resource.resource_id == resource_id)

        # I think apply_resource_deletion_policy() would not work here, since
        # Resource does not have a defined foreign key relationship with
        # itself.
        if deletion_policy is DeletionPolicy.DELETED:
            stmt = stmt.where(Resource.is_deleted == True)  # noqa: E712
        elif deletion_policy is DeletionPolicy.NOT_DELETED:
            stmt = stmt.where(Resource.is_deleted == False)  # noqa: E712

        resource = self._session.scalar(stmt)
        return resource

    def get_draft_modification_by_user(
        self,
        user: User | int,
        resource: Resource | ResourceSnapshot | int,
    ) -> DraftResource | None:
        """
        Get the first draft modification created by the given user, of the
        given resource.

        Args:
            user: A User object or user_id integer primary key value
            resource: A resource, snapshot, or resource_id integer primary key
                value

        Returns:
            A DraftResource, or None if one was not found

        Raises:
            EntityDoesNotExistError: if the user or resource do not exist
            EntityDeletedError: if the user or resource are deleted
        """

        assert_user_exists(self._session, user, DeletionPolicy.NOT_DELETED)
        assert_resource_exists(self._session, resource, DeletionPolicy.NOT_DELETED)

        user_id = get_user_id(user)
        resource_id = get_resource_id(resource)

        stmt = sa.select(DraftResource).where(
            DraftResource.payload["resource_id"].as_integer() == resource_id,
            DraftResource.user_id == user_id,
        )

        draft = self._session.scalar(stmt)
        return draft

    def get_num_draft_modifications(
        self,
        resource: Resource | ResourceSnapshot | int,
        except_user: User | int | None = None,
    ) -> int:
        """
        Get the number of draft modifications of the given resource, which
        were not created by the given user.

        Args:
            resource: The resource whose drafts should be counted
            except_user: The user whose drafts should not be counted; None
                to count them all

        Returns:
            A draft count

        Raises:
            EntityDoesNotExistError: if except_user is given, but it does not
                exist, or if the given resource does not exist
            EntityDeletedError: if except_user is given, but it is deleted,
                or if the given resource is deleted
        """

        if except_user is not None:
            assert_user_exists(self._session, except_user, DeletionPolicy.NOT_DELETED)

        assert_resource_exists(self._session, resource, DeletionPolicy.NOT_DELETED)

        resource_id = get_resource_id(resource)

        stmt = (
            sa.select(sa.func.count())
            .select_from(DraftResource)
            .where(
                DraftResource.payload["resource_id"].as_integer() == resource_id,
            )
        )

        if except_user is not None:
            user_id = get_user_id(except_user)
            stmt = stmt.where(DraftResource.user_id != user_id)

        count = self._session.scalar(stmt)

        # for mypy: a "select count() ..." statement should always return a
        # result.
        assert count is not None

        return count

    def get_by_filters_paged(
        self,
        draft_type: DraftType,
        resource_type: str,
        user: User | int,
        group: Group | int | None = None,
        base_resource_id: int | None = None,
        page_start: int = 0,
        page_length: int = -1,
    ) -> tuple[Sequence[DraftResource], int]:
        """
        Get some drafts according to search criteria.

        Args:
            draft_type: the type of draft to get
            resource_type: Only get drafts for this resource type
            user: Only get drafts created by this user
            group: Only get drafts owned by this group; None to not filter by
                group owner
            base_resource_id: Only get drafts with this base resource ID; None
                to not filter by base resource ID
            page_start: A row index where the returned page should start
            page_length: A row count representing the page length; use <= 0
                for unlimited length

        Returns:
            A 2-tuple including a page of DraftResource objects, and a count
            of the total number of drafts matching the criteria

        Raises:
            EntityDoesNotExistError: if the given user does not exist, or if
                a group is given but it does not exist, or if a
                base_resource_id is given, but does not refer to an existing
                resource
            EntityDeletedError: if the given user is deleted, or if a group is
                given but it is deleted, or if base_resource_id is given but
                refers to a deleted resource
        """

        assert_user_exists(self._session, user, DeletionPolicy.NOT_DELETED)

        user_id = get_user_id(user)

        if group is None:
            group_id = None
        else:
            assert_group_exists(self._session, group, DeletionPolicy.NOT_DELETED)
            group_id = get_group_id(group)

        if base_resource_id is not None:
            assert_resource_exists(
                self._session, base_resource_id, DeletionPolicy.NOT_DELETED
            )

        filters = [
            DraftResource.user_id == user_id,
            DraftResource.resource_type == resource_type,
        ]

        if group_id is not None:
            filters.append(DraftResource.group_id == group_id)

        if base_resource_id is not None:
            filters.append(
                DraftResource.payload["base_resource_id"].as_integer()
                == base_resource_id
            )

        if draft_type is DraftType.RESOURCE:
            filters.append(
                DraftResource.payload["resource_id"].as_integer() == None  # noqa: E711
            )
        elif draft_type is DraftType.MODIFICATION:
            filters.append(
                DraftResource.payload["resource_id"].as_integer() != None  # noqa: E711
            )
        # else: if DraftType.ALL, don't filter

        count_stmt = (
            sa.select(sa.func.count()).select_from(DraftResource).where(*filters)
        )

        total_num_drafts = self._session.scalar(count_stmt)

        # for mypy: a "select count() ..." statement should always return a
        # result.
        assert total_num_drafts is not None

        drafts: Sequence[DraftResource]
        if total_num_drafts == 0:
            drafts = []

        else:
            # *must* enforce a sort order for consistent paging
            drafts_stmt = (
                sa.select(DraftResource)
                .where(*filters)
                .order_by(DraftResource.draft_resource_id)
                .offset(page_start)
            )

            if page_length > 0:
                drafts_stmt = drafts_stmt.limit(page_length)

            drafts = self._session.scalars(drafts_stmt).all()

        return drafts, total_num_drafts

    def update(
        self,
        draft: DraftResource | int,
        payload: dict[str, Any],
        resource_snapshot: ResourceSnapshot | int | None = None,
    ) -> DraftResource:
        """
        Replace the payload of the given draft with the given payload, and
        optionally update which snapshot it refers to.

        Args:
            draft: An existing or ID of an existing DraftResource
            payload: A payload to set
            resource_snapshot: A resource snapshot or ID, used to update a
                draft modification to a different snapshot, or None to leave
                the snapshot ID as-is.  This argument must be None for draft
                resources.

        Returns:
            An updated DraftResource object.  If a draft object was passed in,
            the same one is returned.

        Raises:
            DraftDoesNotExistError: if the draft does not exist
            DraftModificationRequiredError: if attempting to change the
                resource snapshot ID on a draft resource
            DraftSnapshotIdInvalidError: if a resource snapshot change is
                attempted on a draft modification, but the new snapshot
                is of a different resource than the old one
            EntityDoesNotExistError: if resource_snapshot does not exist
        """

        # Really need the DraftResource object here
        if isinstance(draft, int):
            temp = self.get(draft)
            if not temp:
                raise DraftDoesNotExistError(draft_resource_id=draft)
            draft = temp
        else:
            assert_draft_exists(self._session, draft)

        if resource_snapshot is not None:
            # If the existing draft's resource_snapshot_id property is null,
            # it must be for a draft resource, not a draft modification.
            # Therefore, a resource_snapshot_id change is not applicable.
            if draft.payload["resource_snapshot_id"] is None:
                raise DraftModificationRequiredError(draft.draft_resource_id)

            assert_snapshot_exists(self._session, resource_snapshot)
            resource_snapshot_id = get_resource_snapshot_id(resource_snapshot)

            if resource_snapshot_id is not None:
                # Ensure the new snapshot is still a snapshot of the same
                # resource as the old one
                _assert_snapshot_and_resource_id_match(
                    self._session,
                    draft.payload["resource_id"],
                    resource_snapshot_id,
                )

        else:
            resource_snapshot_id = None

        draft.payload["resource_data"] = payload
        if resource_snapshot_id is not None:
            draft.payload["resource_snapshot_id"] = resource_snapshot_id
        draft.last_modified_on = datetime.datetime.now(tz=datetime.UTC)

        return draft

    def delete(self, draft: DraftResource | int) -> None:
        """
        Delete the given draft.

        Args:
            draft: An existing or ID of an existing DraftResource

        Raises:
            DraftDoesNotExistError: if the draft does not exist
        """

        if draft_exists(self._session, draft):
            if isinstance(draft, int):
                stmt = sa.delete(DraftResource).where(
                    DraftResource.draft_resource_id == draft
                )
                self._session.execute(stmt)
            else:
                self._session.delete(draft)

        else:
            raise DraftDoesNotExistError(draft_resource_id=get_draft_id(draft))

    def has_draft_modifications(
        self,
        resources: Iterable[Resource | ResourceSnapshot | int],
        user: User | int | None = None,
    ) -> set[int]:
        """
        Determine which of the given resources have draft modifications.  If
        a user is given, filter results to the modifications created by that
        user.

        Args:
            resources: The resources to check
            user: A User object or user_id integer primary key value, or None

        Returns:
            A set of resource IDs
        """
        resource_ids = []

        for resource in resources:
            resource_id = get_resource_id(resource)
            if resource_id is not None:
                resource_ids.append(resource_id)

        if not resource_ids:
            resource_ids_with_drafts = set()

        else:
            stmt = sa.select(DraftResource.payload["resource_id"].as_integer()).where(
                DraftResource.payload["resource_id"].as_integer().in_(resource_ids),
            )

            if user is None:
                user_id = None
            else:
                user_id = get_user_id(user)

            if user_id is not None:
                stmt = stmt.where(DraftResource.user_id == user_id)

            resource_ids_with_drafts = set(self._session.scalars(stmt))

        return resource_ids_with_drafts

    def has_draft_modification(
        self,
        resource: Resource | ResourceSnapshot | int,
        user: User | int | None = None,
    ) -> bool:
        """
        Determine whether given resource has a draft modification.  If a user
        is given, return True only if the given resource has a draft
        modification which was created by that user.

        Args:
            resource: The resource to check
            user: A User object or user_id integer primary key value, or None

        Returns:
            True if the resource has a draft modification, else False
        """
        result: bool | None

        resource_id = get_resource_id(resource)
        if resource_id is None:
            result = False
        else:
            stmt: sa.Select = (
                sa.select(sa.literal_column("1"))
                .select_from(DraftResource)
                .where(DraftResource.payload["resource_id"].as_integer() == resource_id)
            )

            if user is None:
                user_id = None
            else:
                user_id = get_user_id(user)

            if user_id is not None:
                stmt = stmt.where(DraftResource.user_id == user_id)

            exists_stmt = sa.select(stmt.exists())

            result = self._session.scalar(exists_stmt)

            # a "SELECT EXISTS(...)" should always return a row (true/false).
            assert result is not None

        return result


def _assert_snapshot_and_resource_id_match(
    session: CompatibleSession[S], resource_id: int, resource_snapshot_id: int
):
    """
    Ensure the snapshot given is a snapshot of the resource given.

    Args:
        session: An SQLAlchemy session
        resource_id: A resource ID
        resource_snapshot_id: A resource snapshot ID

    Raises:
        DraftSnapshotIdInvalidError: if resource_snapshot_id refers to a
            snapshot of a different resource than that referred to by
            resource_id
    """
    stmt: sa.Select = (
        sa.select(sa.literal_column("1"))
        .select_from(ResourceSnapshot)
        .where(
            ResourceSnapshot.resource_id == resource_id,
            ResourceSnapshot.resource_snapshot_id == resource_snapshot_id,
        )
    )
    result = session.scalar(sa.select(stmt.exists()))
    if not result:
        raise DraftSnapshotIdInvalidError(
            resource_id,
            resource_snapshot_id,
        )
