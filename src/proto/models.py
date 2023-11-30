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
from typing import Any, Optional, TypedDict


class PrototypeDb(TypedDict):
    """A simple key-value data store for prototyping/testing purposes.

    Attributes:
        users: The users table containing all registered users.

    Important:
        This is not thread-safe, do not use this pattern in a real app!
    """

    users: dict[str, User]


db: PrototypeDb = PrototypeDb(users={})


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
    password: Optional[str]
    deleted: bool

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


if __name__ == "__main__":
    import doctest

    doctest.testmod(verbose=True)
