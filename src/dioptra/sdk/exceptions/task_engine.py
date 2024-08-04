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
from collections.abc import Iterable
from typing import Any, Optional

import dioptra.task_engine.types

from .base import BaseTaskEngineError


class StepError(BaseTaskEngineError):
    """
    An error which can occur or exist within the context of a particular step
    of a task graph.  This class has support for storing the contextual step
    name and producing a better error message.
    """

    def __init__(self, message: str, context_step_name: Optional[str] = None) -> None:
        """
        Initialize this error instance.

        Args:
            message: An error message
            context_step_name: The name of the step which was the context of
                the error, or None.  If None, the step name can be populated
                later, e.g. filled in at a higher stack frame where the info is
                known.
        """

        super().__init__(message)

        # Step name which is the context for this error.
        self.context_step_name = context_step_name

        self.__message = message

    def __str__(self) -> str:
        """
        Override string representation such that it depends on what context we
        have for the error.  With more context, we can produce a better error
        message.

        Returns:
            A composed error message string
        """
        msg_parts = []
        if self.context_step_name:
            msg_parts.append('In step "{}": '.format(self.context_step_name))

        msg_parts.append(self.__message)

        return "".join(msg_parts)


class StepNotFoundError(StepError):
    """A reference to a nonexistent step."""

    def __init__(self, step_name: str, context_step_name: Optional[str] = None) -> None:
        super().__init__("Step not found: " + step_name, context_step_name)

        self.step_name = step_name


class OutputNotFoundError(StepError):
    """A reference to a nonexistent output of an existing step."""

    def __init__(
        self, step_name: str, output_name: str, context_step_name: Optional[str] = None
    ) -> None:
        super().__init__(
            'Unrecognized output of step "{}": {}'.format(step_name, output_name),
            context_step_name,
        )

        self.step_name = step_name
        self.output_name = output_name


class IllegalOutputReferenceError(StepError):
    """A reference to a multi-output step did not name the desired output."""

    def __init__(self, step_name: str, context_step_name: Optional[str] = None) -> None:
        super().__init__(
            "An output name is required when referring to a step with more"
            " than one output: " + step_name,
            context_step_name,
        )

        self.step_name = step_name


class NonIterableTaskOutputError(StepError):
    """
    Task output was defined using a list, but the task invocation did not
    return an iterable value.
    """

    def __init__(self, value: Any, context_step_name: Optional[str] = None) -> None:
        super().__init__(
            "Task output was defined using a list, but the task invocation did"
            " not return an iterable value: {} ({})".format(value, type(value)),
            context_step_name,
        )

        self.value = value


class UnresolvableReferenceError(StepError):
    """
    A reference did not resolve and does not match any global parameter or
    step (so we don't know what the intent was), or the reference was to the
    output of a step which was not declared to produce any output.
    """

    def __init__(
        self, reference_name: str, context_step_name: Optional[str] = None
    ) -> None:
        super().__init__("Unresolvable reference: " + reference_name, context_step_name)

        self.reference_name = reference_name


class TaskPluginNotFoundError(StepError):
    """A reference to a nonexistent task plugin."""

    def __init__(
        self, task_plugin_short_name: str, context_step_name: Optional[str] = None
    ) -> None:
        super().__init__(
            "Task plugin not found: " + task_plugin_short_name, context_step_name
        )

        self.task_plugin_short_name = task_plugin_short_name


class MissingTaskPluginNameError(StepError):
    """
    A step description was malformed: it was missing a task plugin short name.
    """

    def __init__(self, context_step_name: Optional[str] = None) -> None:
        super().__init__("Step is missing a task plugin name", context_step_name)


class MissingGlobalParametersError(BaseTaskEngineError):
    """
    A value could not be obtained for some task graph global parameter(s).
    """

    def __init__(self, parameter_names: Iterable[str]) -> None:
        super().__init__(
            "Missing values for global parameters: " + ", ".join(parameter_names)
        )

        self.parameter_names = parameter_names


class IllegalPluginNameError(BaseTaskEngineError):
    """A task was defined with an illegal plugin name."""

    def __init__(self, plugin_name: str) -> None:
        super().__init__(
            "A task plugin must be a dot-delimited string of at least two"
            " components: " + plugin_name
        )

        self.plugin_name = plugin_name


class StepReferenceCycleError(BaseTaskEngineError):
    """A cycle was detected in the step graph."""

    def __init__(self, cycle: Iterable[str]) -> None:
        super().__init__("Step cycle detected: {}".format(" > ".join(cycle)))

        self.cycle = cycle


class DioptraTypeError(BaseTaskEngineError):
    # Can't name this "TypeError", since that's a builtin Python exception
    # type!
    """
    An error which can occur or exist within the context of a particular
    top-level type definition.  This class has support for storing the
    contextual type name and producing a better error message.
    """

    def __init__(self, message: str, context_type_name: Optional[str] = None) -> None:
        """
        Initialize this error instance.

        :param message: An error message
        :param context_type_name: The name of the type which was the context of
            the error, or None.  If None, the type name can be populated later,
            e.g. filled in at a higher stack frame where the info is known.
        """

        super().__init__(message)

        # Step name which is the context for this error.
        self.context_type_name = context_type_name

        self.__message = message

    def __str__(self) -> str:
        """
        Override string representation such that it depends on what context we
        have for the error.  With more context, we can produce a better error
        message.

        :return: A composed error message string
        """
        msg_parts = []
        if self.context_type_name:
            msg_parts.append(
                'In definition of type "{}": '.format(self.context_type_name)
            )

        msg_parts.append(self.__message)

        return "".join(msg_parts)


class TypeNotFoundError(DioptraTypeError):
    """
    A reference to an unknown type was found.
    """

    def __init__(self, type_name: str, context_type_name: Optional[str] = None) -> None:
        message = "Type not found: " + type_name
        super().__init__(message, context_type_name)

        self.type_name = type_name


class NonSimpleSuperTypeError(DioptraTypeError):
    """
    A simple type definition referenced a super-type which was not simple.
    """

    def __init__(
        self, super_type_name: str, context_type_name: Optional[str] = None
    ) -> None:
        message = "Super-types must be simple: " + super_type_name
        super().__init__(message, context_type_name)

        self.super_type_name = super_type_name


class InvalidKeyTypeError(DioptraTypeError):
    """
    A mapping structured type was defined with an invalid key type.
    """

    def __init__(
        self,
        invalid_key_type: "dioptra.task_engine.types.Type",
        context_type_name: Optional[str] = None,
    ) -> None:
        message = "Invalid key type; require string or integer: {!s}".format(
            invalid_key_type
        )

        super().__init__(message, context_type_name)

        self.invalid_key_type = invalid_key_type


class TooManyTypeStructuresError(DioptraTypeError):
    """
    A type definition included more than one structure type.
    """

    def __init__(
        self,
        structure_types: Iterable["dioptra.task_engine.types.StructureType"],
        context_type_name: Optional[str] = None,
    ) -> None:
        message = (
            "A type definition may include at most one structure type." "  Found: {}"
        ).format(", ".join(structure_type.name for structure_type in structure_types))

        super().__init__(message, context_type_name)

        self.structure_types = structure_types


class InvalidTypeStructureDefinitionError(DioptraTypeError):
    """
    The definition of a structured type was invalid.
    """

    def __init__(self, message: str, context_type_name: Optional[str] = None) -> None:
        super().__init__(message, context_type_name)


class BuiltinTypeRedefinitionError(DioptraTypeError):
    """
    A type definition tried to redefine a builtin type.
    """

    def __init__(self, builtin_type_name: str) -> None:
        message = "Redefinition of builtin types not allowed: {}".format(
            builtin_type_name
        )

        super().__init__(message)

        self.builtin_type_name = builtin_type_name


class AnonymousSimpleTypeError(DioptraTypeError):
    """
    An attempt to create an anonymous type from a null type definition (which
    signifies a simple type).
    """

    def __init__(self) -> None:
        message = (
            "Unable to create an anonymous type from a null type"
            " definition: simple types can't be anonymous."
        )

        super().__init__(message)


class TypeReferenceCycleError(BaseTaskEngineError):
    """A cycle was detected in a set of type definitions."""

    def __init__(self, cycle: Iterable[str]) -> None:
        super().__init__("Type reference cycle detected: {}".format(" > ".join(cycle)))

        self.cycle = cycle
