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

from .base import CollectionClient, DioptraFile

T = TypeVar("T")


class EchoesCollectionClient(CollectionClient[T]):
    """The client for managing Dioptra's /echoes collection.

    Attributes:
        name: The name of the collection.
    """

    name: ClassVar[str] = "echoes"

    def create(
        self,
        test_files: list[DioptraFile] | None = None,
        test_string: str | None = None,
    ) -> T:
        data: dict[str, Any] = {}
        files: dict[str, DioptraFile | list[DioptraFile]] = {}

        if test_string is not None:
            data["testString"] = test_string

        if test_files:
            files["testFiles"] = test_files

        return self._session.post(self.url, "", data=data or None, files=files or None)

    def create_single(
        self, test_file: DioptraFile | None = None, test_string: str | None = None
    ) -> T:
        data: dict[str, Any] = {}
        files: dict[str, DioptraFile | list[DioptraFile]] = {}

        if test_string is not None:
            data["testString"] = test_string

        if test_file:
            files["testFile"] = test_file

        return self._session.post(
            self.url, "singleFile", data=data or None, files=files or None
        )
