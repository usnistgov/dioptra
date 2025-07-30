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
import abc as abc
from pathlib import Path
from typing import Any


class ArtifactTaskInterface(abc.ABCMeta):
    """
    Interface class which exposes the logic for serialization and deserialization of an
    artifact.

    It is expected that implementations will override all methods in this interface.
    """

    @staticmethod
    @abc.abstractmethod
    def serialize(working_dir: Path, name: str, contents: Any, **kwargs) -> Path:
        """
        Called to serialize an artifact. The value and type of contents is dependent on
        the artifact output declaration.

        Arguments:
            working_dir: the path to which any artifact should be serialized
            name: the name of the artifact; in general, the name should be used as the
                stem or name of the file
            contents: the contents to serialize. Specific implementations should specify
                which type they support.
            kwargs: any additional keyword arguments that this serializer uses. Keyword
                arguments are added to the `validation` method below

        Returns:
            A Path pointing to the location where the artifact has been serialized. This
            could be either a directory or a file depending on the type of artifact.
        """
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def deserialize(working_dir: Path, path: str, **kwargs) -> Any:
        """
        Called to deserialize an artifact.

        Arguments:
            working_dir: the working directory which serves as the directory to process
                the artifact in. Any intermediate files created as part of the
                deserialization process should be produced in this directory.
            path: the path to the artifact to deserialize and is relative to the value
                of `working_dir`. This means implementations should access the artifact
                by creating a path object along the lines of `Path(working_dir, path)`.
            kwargs: any extra keyword arguments to use as part of deserialization
                (unused at this time)

        Returns:
            The result of deserialization. This could be any type or value.
        """
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def validation() -> dict[str, Any] | None:
        """
        The validation is inserted into the JSON Schema to validate any extra keyword
        arguments that are passed to the serialization method of this artifact task. The
        validation indicates the name and type of the arguments. See
        https://json-schema.org/docs for more information. The version of JSON schema
        used at this time is https://json-schema.org/draft/2020-12/schema.

        Example:
            The following dictionary specifies three extra keyword arguments of
            `foo`, `bar`, and `baz` and their types.
                - `foo` is a string.
                - `bar` is an enumerated value with three possible values.
                - `baz` is an integer.

            .. code-block:: python
                {
                    "foo": {"type": "string"},
                    "bar": {"enum": ["value1", "value2", "value3"]},
                    "baz": {"type": "integer"},
                }

        Returns:
            A dictionary containing the validation information for the keyword arguments
            to serialize or `None` if no extra keyword arguments are used.
        """
        raise NotImplementedError

    @staticmethod
    @abc.abstractmethod
    def name() -> str:
        """
        The name of the artifact task.

        Returns:
            The name of this particular artifact task instance.
        """
        raise NotImplementedError
