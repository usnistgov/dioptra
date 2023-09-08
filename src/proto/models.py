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
from typing import Any, TypedDict, Union


class PrototypeDb(TypedDict):
    """A simple key-value data store for prototyping/testing purposes.

    Attributes:
        users: The users table containing all registered users.

    Important:
        This is not thread-safe, do not use this pattern in a real app!
    """

    users: dict[str, User]
    groups: dict[str, Group]
    resources: dict[str, Dioptra_Resource]


db: PrototypeDb = PrototypeDb(users={}, groups={}, resources= {})


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
    roles: list[Role]

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
    
    def add_role(self, role: Role) -> None:
        """Give a user a role on an item.

        Returns:
            None
        """
        return self.roles.append(role)
    
@dataclass
class Dioptra_Resource(object):
    """A registered resource of the application.

    Attributes:
        id: The unique identifier of the resource.
        alternative_id: A UUID as a 32-character lowercase hexadecimal string that
            serves as the user's alternative identifier. The alternative_id is
            changed when the user's password is changed or the user revokes all
            active sessions via a full logout.
        name: The user's username used for logging in.
        deleted: Whether the resource has been deleted.
    """

    id: int
    alternative_id: str
    name: str
    owner: User
    is_public: bool # not sure if useful
    shared_with: list[Group] #for reading/ writing
    #shared_with_write: list[Group] #for wriiting
    deleted: bool

    

    @property
    def is_active(self) -> bool:
        """Return True if the user account is active, False otherwise."""
        return not self.deleted

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
    
    def share_read(self, actor):
        self.shared_with.append(actor)

    def unshare_read(self, actor):
        self.shared_with.remove(actor)

    # def share_write(self, actor):
    #     self.shared_with_write.append(actor)

    # def unshare_write(self, actor):
    #     self.shared_with_write.remove(actor)
    
@dataclass
class Group(object):
    """A registered group of the application.

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
    is_public: bool # not sure if useful
    deleted: bool


     #resources:list[Dioptra_Resource] # I think this is unncessary and can be done with fields?

    

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
class Role:
    name: str
    resource: Union[ Group, Dioptra_Resource]


if __name__ == "__main__":
    import doctest

    doctest.testmod(verbose=True)
