"""The data models representing application entities.

Examples:
    >>> user = User(
    ...     id=1,
    ...     alternative_id="51da4e0c1cc34d558f7e2617905572a4",
    ...     name="user",
    ...     password="password",
    ...     deleted=False,
    ... )
    >>> user_dict = dict(
    ...     id=1,
    ...     alternative_id="51da4e0c1cc34d558f7e2617905572a4",
    ...     name="user",
    ...     password="password",
    ...     deleted=False,
    ... )
    >>> user.to_json() == user_dict
    True
    >>> user.is_authenticated
    True
    >>> user.is_active
    True
    >>> user.is_anonymous
    False
    >>> user.get_id()
    '51da4e0c1cc34d558f7e2617905572a4'
    >>> user.deleted = True
    >>> user.is_active
    False
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, TypedDict, cast


class PrototypeDb(TypedDict):
    """A simple key-value data store for prototyping/testing purposes.

    Attributes:
        users: The users table containing all registered users.

    Important:
        This is not thread-safe, do not use this pattern in a real app!
    """

    users: dict[str, User]
    groups: dict[str, Group]
    group_memberships: dict[str, GroupMembership]
    resources: dict[str, PrototypeResource]
    shared_resources: dict[str, SharedPrototypeResource]


db: PrototypeDb = PrototypeDb(
    users={},
    groups={},
    group_memberships={},
    resources={},
    shared_resources={},
)


@dataclass
class User(object):
    """A registered user of the application.

    Attributes:
        id: The unique identifier of the user.
        alternative_id: A UUID as a 32-character lowercase hexadecimal string that
            serves as the user's alternative identifier. The alternative_id is
            changed when the user's password is changed or the user revokes all
            active sessions via a full logout.
        name: The user's username used for logging in.
        password: The user's password.
        deleted: Whether the user account has been deleted.
    """

    id: int
    alternative_id: str
    name: str
    password: str
    deleted: bool

    @property
    def groups(self) -> list[GroupMembership]:
        """A list of the user's group memberships."""
        return [x for x in db["group_memberships"].values() if self.id == x.user_id]

    @property
    def is_authenticated(self) -> bool:
        """Return True if the user is authenticated, False otherwise."""
        return self.is_active

    @property
    def is_active(self) -> bool:
        """Return True if the user account is active, False otherwise."""
        return not self.deleted

    @property
    def is_anonymous(self) -> bool:
        """Return True if the user is registered, False otherwise."""
        return False

    def get_id(self) -> str:
        """Get the user's session identifier.

        Returns:
            The user's identifier as a string.
        """
        return str(self.alternative_id)

    def to_json(self) -> dict[str, Any]:
        """Convert the user model to a JSON serializable dictionary.

        Returns:
            A JSON serializable dictionary containing the user's information.
        """
        return asdict(self)


@dataclass
class Group(object):
    """An application group.

    Attributes:
        id: The unique identifier of the group.
        name: Human-readable name for the group.
        creator_id: The id for the user that created the group.
        owner_id: The id for the user that owns the group.
        deleted: Whether the group has been deleted.
    """

    id: int
    name: str
    creator_id: int
    owner_id: int
    deleted: bool

    @property
    def creator(self) -> User:
        """The user that created the group."""
        return db["users"][str(self.creator_id)]

    @property
    def owner(self) -> User:
        """The user that owns the group."""
        return db["users"][str(self.owner_id)]

    @property
    def users(self) -> list[GroupMembership]:
        """The users that are members of the group."""
        return [x for x in db["group_memberships"].values() if self.id == x.group_id]

    @property
    def resources(self) -> list[PrototypeResource]:
        """The resources that the group owns."""
        return [x for x in db["resources"].values() if self.id == x.owner.id]

    @property
    def shared_resources(self) -> list[SharedPrototypeResource]:
        """The resources that have been shared with the group."""
        return [x for x in db["shared_resources"].values() if self.id == x.group.id]

    def check_membership(self, user: User) -> bool:
        """Check if the user is a member of the group.

        Args:
            user: The user to check.

        Returns:
            True if the user is a member of the group, False otherwise.
        """
        return user.id in {x.user_id for x in self.users}


@dataclass
class GroupMembership(object):
    """A mapping of users to groups.

    Attributes:
        group_id: The id for the group that the user is a member of.
        user_id: The id for the user that is a member of the group.
        read: Whether the user can read the group's resources.
        write: Whether the user can write to the group's resources.
        share_read: Whether the user can attach read permissions when sharing a group
            resource.
        share_write: Whether the user can attach write permissions when sharing a
            group resource.
    """

    user_id: int
    group_id: int
    read: bool
    write: bool
    share_read: bool
    share_write: bool

    @property
    def user(self) -> User:
        """The user that is a member of the group."""
        return db["users"][str(self.user_id)]

    @property
    def group(self) -> Group:
        """The group that the user is a member of."""
        return db["groups"][str(self.group_id)]


@dataclass
class PrototypeResource(object):
    """A representation of a resource in the application.

    Attributes:
        id: The unique identifier of the resource.
        creator_id: The id for the user that created the resource.
        owner_id: The id for the group that owns the resource.
        deleted: Whether the resource has been deleted.
    """

    id: int
    creator_id: int
    owner_id: int
    deleted: bool

    @property
    def creator(self) -> User:
        """The user that created the resource."""
        return db["users"][str(self.creator_id)]

    @property
    def owner(self) -> Group:
        """The group that owns the resource."""
        return db["groups"][str(self.owner_id)]

    @property
    def shares(self) -> list[SharedPrototypeResource]:
        """The groups that the resource is shared with."""
        return [x for x in db["shared_resources"].values() if self.id == x.resource.id]

    def check_permission(self, user: User, action: str) -> bool:
        """Check if the user has permission to perform the specified action.

        Args:
            user: The user to check.
            action: The action to check.

        Returns:
            True if the user has permission to perform the action, False otherwise.
        """
        membership = next((x for x in self.owner.users if x.user_id == user.id), None)

        if membership is None:
            return False

        return cast(bool, getattr(membership, action))


@dataclass
class SharedPrototypeResource(object):
    """A representation of a shared resource in the application.

    Attributes:
        id: The unique identifier of the resource.
        creator_id: The id for the user that created the shared resource.
        resource_id: The id for the resource that is being shared.
        group_id: The id for the group that the resource is being shared with.
        deleted: Whether the shared resource has been deleted.
        readable: Whether the shared resource is readable.
        writable: Whether the shared resource is writable.
    """

    id: int
    creator_id: int
    resource_id: int
    group_id: int
    deleted: bool
    readable: bool
    writable: bool

    @property
    def creator(self) -> User:
        """The user that created the shared resource."""
        return db["users"][str(self.creator_id)]

    @property
    def resource(self) -> PrototypeResource:
        """The resource that is being shared."""
        return db["resources"][str(self.resource_id)]

    @property
    def group(self) -> Group:
        """The group that the resource is being shared with."""
        return db["groups"][str(self.group_id)]

    def check_permission(self, user: User, action: str) -> bool:
        """Check if the user has permission to perform the specified action.

        Args:
            user: The user to check.
            action: The action to check.

        Returns:
            True if the user has permission to perform the action, False otherwise.
        """
        membership = next((x for x in self.group.users if x.user_id == user.id), None)

        if membership is None:
            return False

        group_permission = cast(bool, getattr(membership, action))
        share_permission = cast(
            bool, getattr(self, {"read": "readable", "write": "writable"}[action])
        )

        return group_permission and share_permission


if __name__ == "__main__":
    import doctest

    doctest.testmod(verbose=True)
