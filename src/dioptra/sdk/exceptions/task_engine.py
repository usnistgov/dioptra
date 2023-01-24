from collections.abc import Iterable
from typing import Any

from .base import BaseTaskEngineError


class StepError(BaseTaskEngineError):
    """
    An error which can occur or exist within the context of a particular step
    of a task graph.  This class has support for storing the contextual step
    name and producing a better error message.
    """

    def __init__(self, message: str, context_step_name: str = None) -> None:
        """
        Initialize this error instance.

        :param message: An error message
        :param context_step_name: The name of the step which was the context of
            the error, or None.  If None, the step name can be populated later,
            e.g. filled in at a higher stack frame where the info is known.
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

        :return: A composed error message string
        """
        msg_parts = []
        if self.context_step_name:
            msg_parts.append('In step "{}": '.format(self.context_step_name))

        msg_parts.append(self.__message)

        return "".join(msg_parts)


class StepNotFoundError(StepError):
    """A reference to a non-existent step."""

    def __init__(self, step_name: str, context_step_name: str = None) -> None:
        super().__init__("Step not found: " + step_name, context_step_name)

        self.step_name = step_name


class OutputNotFoundError(StepError):
    """A reference to a non-existent output of an existing step."""

    def __init__(
        self, step_name: str, output_name: str, context_step_name: str = None
    ) -> None:
        super().__init__(
            'Unrecognized output of step "{}": {}'.format(step_name, output_name),
            context_step_name,
        )

        self.step_name = step_name
        self.output_name = output_name


class IllegalOutputReferenceError(StepError):
    """A reference to a multi-output step did not name the desired output."""

    def __init__(self, step_name: str, context_step_name: str = None) -> None:
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

    def __init__(self, value: Any, context_step_name: str = None) -> None:

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

    def __init__(self, reference_name: str, context_step_name: str = None) -> None:
        super().__init__("Unresolvable reference: " + reference_name, context_step_name)

        self.reference_name = reference_name


class TaskPluginNotFoundError(StepError):
    """A reference to a non-existent task plugin."""

    def __init__(
        self, task_plugin_short_name: str, context_step_name: str = None
    ) -> None:
        super().__init__(
            "Task plugin not found: " + task_plugin_short_name, context_step_name
        )

        self.task_plugin_short_name = task_plugin_short_name


class MissingTaskPluginNameError(StepError):
    """
    A step description was malformed: it was missing a task plugin short name.
    """

    def __init__(self, context_step_name: str = None) -> None:
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
