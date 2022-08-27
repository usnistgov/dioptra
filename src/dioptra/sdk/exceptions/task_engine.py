from .base import BaseTaskEngineError


class StepError(BaseTaskEngineError):
    """
    An error which occurred or exists within the context of a particular step
    of a task graph.  This class has support for storing the contextual step
    name and producing a better error message.
    """
    def __init__(self, message, context_step_name=None):
        """
        Initialize this error instance.

        :param message: An error message
        :param step_name: The name of the step which was the context of the
            error, or None.  If None, the step name can be populated later,
            e.g. filled in at a higher stack frame where the info is known.
        """

        super().__init__(message)

        # Step name which is the context for this error.
        self.context_step_name = context_step_name

        self.__message = message

    def __str__(self):
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


class StepNotFound(StepError):
    """A reference to a non-existent step."""

    def __init__(self, step_name, context_step_name=None):
        super().__init__(
            "Step not found: " + step_name,
            context_step_name
        )

        self.step_name = step_name


class OutputNotFound(StepError):
    """A reference to a non-existent output of an existing step."""

    def __init__(self, step_name, output_name, context_step_name=None):
        super().__init__(
            'Unrecognized output of step "{}": {}'.format(
                step_name, output_name
            ),
            context_step_name
        )

        self.step_name = step_name
        self.output_name = output_name


class IllegalOutputReference(StepError):
    """A reference to a multi-output step did not name the desired output."""

    def __init__(self, step_name, context_step_name=None):
        super().__init__(
            'An output name is required when referring to a step with more'
            ' than one output: ' + step_name,
            context_step_name
        )

        self.step_name = step_name


class NonIterableTaskOutputError(StepError):
    """
    Task output was defined using a list, but the task invocation did not
    return an iterable value.
    """

    def __init__(self, value, context_step_name=None):

        super().__init__(
            "Task output was defined using a list, but the task invocation did"
            " not return an iterable value: {} ({})".format(
                value, type(value)
            ),
            context_step_name
        )

        self.value = value


class UnresolvableReference(StepError):
    """
    A reference did not resolve and does not match any global parameter or
    step (so we don't know what the intent was), or the reference was to the
    output of a step which was not declared to produce any output.
    """

    def __init__(self, reference_name, context_step_name=None):
        super().__init__(
            "Unresolvable reference: " + reference_name,
            context_step_name
        )

        self.reference_name = reference_name


class TaskPluginNotFoundError(StepError):
    """A reference to a non-existent task plugin."""

    def __init__(self, task_plugin_short_name, context_step_name=None):
        super().__init__(
            "Task plugin not found: " + task_plugin_short_name,
            context_step_name
        )

        self.task_plugin_short_name = task_plugin_short_name


class PyplugsAutoregistrationError(StepError):
    """
    Pyplugs attempted to auto-register a plugin which is not in a package.
    This causes it to throw an exception.
    """

    def __init__(self, plugin_name, context_step_name=None):
        super().__init__(
            ('Error auto-registering plugin "{}".  Pyplugs\' auto-registration'
             " requires a Python package.  You must either manually register"
             " plugins (e.g. by manually importing their module(s)) before"
             " running this experiment, or move the file with tasks into a"
             " subdirectory which is a package, and update your experiment to"
             " reference task plugins via the package.").format(plugin_name),
            context_step_name
        )

        self.plugin_name = plugin_name


class MissingGlobalParameters(BaseTaskEngineError):
    """
    A value could not be obtained for some task graph global parameter(s).
    """

    def __init__(self, parameter_names):
        super().__init__(
            "Missing values for global parameters: "
            + ", ".join(parameter_names)
        )

        self.parameter_names = parameter_names


class IllegalPluginName(BaseTaskEngineError):
    """A task was defined with an illegal plugin name."""

    def __init__(self, plugin_name):
        super().__init__(
            "A task plugin must be a dot-delimited string of at least two"
            " components: " + plugin_name
        )

        self.plugin_name = plugin_name


class StepReferenceCycleError(BaseTaskEngineError):
    """A cycle was detected in the step graph."""

    def __init__(self, cycle):
        super().__init__(
            "Step cycle detected: {}".format(
                " > ".join(cycle)
            )
        )

        self.cycle = cycle
