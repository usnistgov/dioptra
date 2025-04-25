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

from .base import CollectionClient

T1 = TypeVar("T1")
T2 = TypeVar("T2")


class UsersCollectionClient(CollectionClient[T1, T2]):
    """The client for interacting with the Dioptra API's /users collection.

    Attributes:
        name: The name of the collection.
    """

    name: ClassVar[str] = "users"

    def get(
        self, index: int = 0, page_length: int = 10, search: str | None = None
    ) -> T1:
        """Get a list of Dioptra users.

        Args:
            index: The paging index. Optional, defaults to 0.
            page_length: The maximum number of users to return in the paged response.
                Optional, defaults to 10.
            search: Search for users using the Dioptra API's query language. Optional,
                defaults to None.

        Returns:
            The response from the Dioptra API.
        """
        params: dict[str, Any] = {
            "index": index,
            "pageLength": page_length,
        }

        if search is not None:
            params["search"] = search

        return self._session.get(
            self.url,
            params=params,
        )

    def create(self, username: str, email: str, password: str) -> T1:
        """Creates a Dioptra user.

        Args:
            username: The username of the new user.
            email: The email address of the new user.
            password: The password to set for the new user.

        Returns:
            The response from the Dioptra API.
        """

        return self._session.post(
            self.url,
            json_={
                "username": username,
                "email": email,
                "password": password,
                "confirmPassword": password,
            },
        )

    def get_by_id(self, user_id: str | int) -> T1:
        """Get the user matching the provided id.

        Args:
            user_id: The user id, an integer.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, str(user_id))

    def change_password_by_id(
        self, user_id: str | int, old_password: str, new_password: str
    ) -> T1:
        """Change the password of the user matching the provided id.

        This primary use case for using this over `change_current_user_password` is if
        your password has expired and you need to update it before you can log in.

        Args:
            user_id: The user id, an integer.
            old_password: The user's current password. The password change will fail if
                this is incorrect.
            new_password: The new password to set for the user.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.post(
            self.url,
            str(user_id),
            "password",
            json_={
                "oldPassword": old_password,
                "newPassword": new_password,
                "confirmNewPassword": new_password,
            },
        )

    def get_current(self) -> T1:
        """Get details about the currently logged-in user.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.get(self.url, "current")

    def delete_current_user(self, password: str) -> T1:
        """Delete the currently logged-in user.

        Args:
            password: The password of the currently logged-in user. The deletion will
                fail if this is incorrect.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.delete(self.url, "current", json_={"password": password})

    def modify_current_user(self, username: str, email: str) -> T1:
        """Modify details about the currently logged-in user.

        Args:
            username: The new username for the currently logged-in user.
            email: The new email address for the currently logged-in user.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.put(
            self.url,
            "current",
            json_={"username": username, "email": email},
        )

    def change_current_user_password(self, old_password: str, new_password: str) -> T1:
        """Change the currently logged-in user's password.

        Args:
            old_password: The currently logged-in user's current password. The password
                change will fail if this is incorrect.
            new_password: The new password to set for the currently logged-in user.

        Returns:
            The response from the Dioptra API.
        """
        return self._session.post(
            self.url,
            "current",
            "password",
            json_={
                "oldPassword": old_password,
                "newPassword": new_password,
                "confirmNewPassword": new_password,
            },
        )
