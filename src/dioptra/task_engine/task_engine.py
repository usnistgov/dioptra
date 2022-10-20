import collections
import logging
from collections.abc import Mapping, MutableMapping, Sequence
from typing import Any, Union

import mlflow

import dioptra.pyplugs
from dioptra.sdk.exceptions.task_engine import (
    IllegalOutputReferenceError,
    IllegalPluginNameError,
    MissingGlobalParametersError,
    MissingTaskPluginNameError,
    NonIterableTaskOutputError,
    OutputNotFoundError,
    StepError,
    StepNotFoundError,
    TaskPluginNotFoundError,
    UnresolvableReferenceError,
)
from dioptra.task_engine import util


def _get_logger() -> logging.Logger:
    """
    Get a logger to use for functions in this module.

    :return: The logger
    """
    return logging.getLogger(__name__)


def _resolve_reference(
    reference: str,
    global_parameters: Mapping[str, Any],
    step_outputs: Mapping[str, Mapping[str, Any]]
) -> Any:
    """
    Resolve a reference to a task output or global parameter.

    :param reference: The reference to resolve, without the "$" prefix
    :param global_parameters: The global parameters in use for this run, as a
        mapping from parameter name to value
    :param step_outputs: The step outputs we have thus far.  This is a nested
        mapping: step name => output name => output value.
    :return: The referenced value
    """

    if "." in reference:
        # Must be an <step>.<output> formatted reference
        step_name, output_name = reference.split(".", 1)

        step_output = step_outputs.get(step_name)
        if not step_output:
            raise StepNotFoundError(step_name)

        if output_name not in step_output:
            raise OutputNotFoundError(step_name, output_name)

        value = step_output[output_name]

    else:
        # A bare name may refer to either a global parameter or the only
        # output of a step.  Let's assume prior validation ensured the same
        # name does not occur in both places.
        if reference in global_parameters:
            value = global_parameters[reference]
        elif reference in step_outputs:
            outputs = step_outputs[reference]
            if len(outputs) != 1:
                raise IllegalOutputReferenceError(reference)
            value = next(iter(outputs.values()))
        else:
            raise UnresolvableReferenceError(reference)

    return value


def _resolve_task_parameter_value(
    arg_spec: Any,
    global_parameters: Mapping[str, Any],
    step_outputs: Mapping[str, Mapping[str, Any]]
) -> Any:
    """
    Resolve a specification for one argument of a task invocation, to the
    actual value to be used in the invocation.

    :param arg_spec: The argument specification
    :param global_parameters: The global parameters in use for this run, as a
        mapping from parameter name to value
    :param step_outputs: The step outputs we have thus far.  This is a nested
        mapping: step name => output name => output value.
    :return: The value to use for the given parameter
    """

    if isinstance(arg_spec, str):

        if util.is_reference(arg_spec):
            arg_value = _resolve_reference(
                arg_spec[1:], global_parameters, step_outputs
            )

        elif arg_spec.startswith("$$"):
            # "escaped" dollar sign: replace only the initial "$$" with "$"
            arg_value = arg_spec[1:]

        else:
            arg_value = arg_spec

    elif isinstance(arg_spec, dict):
        arg_value = {
            key: _resolve_task_parameter_value(
                value, global_parameters, step_outputs
            )
            for key, value in arg_spec.items()
        }

    elif isinstance(arg_spec, list):
        arg_value = [
            _resolve_task_parameter_value(
                sub_val, global_parameters, step_outputs
            )
            for sub_val in arg_spec
        ]

    else:
        arg_value = arg_spec

    return arg_value


def _positional_specs_to_args(
    arg_specs: Any,
    global_parameters: Mapping[str, Any],
    step_outputs: Mapping[str, Mapping[str, Any]]
) -> list[Any]:
    """
    Resolve a positional parameter style invocation specification to a list
    of actual parameter values to use in the task invocation.

    :param arg_specs: A single or list of argument specifications.  A single
        (non-list) value is treated as a length one list.
    :param global_parameters: The global parameters in use for this run, as a
        mapping from parameter name to value
    :param step_outputs: The step outputs we have thus far.  This is a nested
        mapping: step name => output name => output value.
    :return: A list of values to use for the invocation
    """
    # Let a non-list value mean the same as a length-1 list, i.e.
    # just one positional argument.
    if not isinstance(arg_specs, list):
        arg_specs = [arg_specs]

    arg_values = [
        _resolve_task_parameter_value(
            arg_spec, global_parameters, step_outputs
        )
        for arg_spec in arg_specs
    ]

    return arg_values


def _kwarg_specs_to_kwargs(
    kwarg_specs: Mapping[str, Any],
    global_parameters: Mapping[str, Any],
    step_outputs: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    """
    Resolve a keyword arg style invocation specification to a mapping of actual
    parameter values to use in the task invocation.

    :param kwarg_specs: A mapping from keyword arg name to value specification
    :param global_parameters: The global parameters in use for this run, as a
        mapping from parameter name to value
    :param step_outputs: The step outputs we have thus far.  This is a nested
        mapping: step name => output name => output value.
    :return: A mapping from parameter name to actual value to use for the
        task invocation
    """
    kwarg_values = {
        kwarg_name: _resolve_task_parameter_value(
            kwarg_value, global_parameters, step_outputs
        )
        for kwarg_name, kwarg_value in kwarg_specs.items()
    }

    return kwarg_values


def _arg_specs_to_args(
    arg_specs: Any,
    global_parameters: Mapping[str, Any],
    step_outputs: Mapping[str, Mapping[str, Any]]
) -> tuple[list[Any], dict[str, Any]]:
    """
    Resolve a task invocation specification to all of the positional and
    keyword arg values to use in the invocation.

    :param arg_specs: The task invocation specification
    :param global_parameters: The global parameters in use for this run, as a
        mapping from parameter name to value
    :param step_outputs: The step outputs we have thus far.  This is a nested
        mapping: step name => output name => output value.
    :return: A 2-tuple including a list of positional values to use in the
        task invocation, followed by a mapping with keyword arg names and
        values.
    """
    arg_values = []
    kwarg_values = {}

    if isinstance(arg_specs, dict):
        if "task" in arg_specs:
            # Use presence of "task" key to signal a more structured
            # arrangement: "args" key for positional args and "kwargs" key for
            # keyword args.
            pos_arg_specs = arg_specs.get("args")
            kwarg_specs = arg_specs.get("kwargs")

            if pos_arg_specs:
                arg_values = _positional_specs_to_args(
                    pos_arg_specs, global_parameters, step_outputs
                )

            if kwarg_specs:
                kwarg_values = _kwarg_specs_to_kwargs(
                    kwarg_specs, global_parameters, step_outputs
                )

        else:
            # Simple kwarg-only invocation
            kwarg_values = _kwarg_specs_to_kwargs(
                arg_specs, global_parameters, step_outputs
            )

    else:
        # A non-dict means a positional-arg-only invocation.
        arg_values = _positional_specs_to_args(
            arg_specs, global_parameters, step_outputs
        )

    return arg_values, kwarg_values


def _update_output_map(
    step_outputs: MutableMapping[str, MutableMapping[str, Any]],
    step_name: str,
    new_output_names: Union[str, Sequence[str]],
    new_outputs: Any
) -> None:
    """
    Update the step outputs mapping according to task metadata regarding output
    name(s), and actual task plugin return value(s).

    :param step_outputs: The step outputs we have thus far.  This a is nested
        mapping: step name => output name => output value.
    :param step_name: The name of the step for which we have output values
    :param new_output_names: Task metadata regarding output names.  This may
        be either a single or list of strings.
    :param new_outputs: The output(s) from the completed step
    """

    log = _get_logger()

    if isinstance(new_output_names, str):
        # If output names is a string, store the task return value directly
        # under that name.
        step_outputs[step_name][new_output_names] = new_outputs

    else:
        # else, new_output_names is a list.  Task plugin return value must
        # be iterable.
        if not util.is_iterable(new_outputs):
            raise NonIterableTaskOutputError(new_outputs, step_name)

        # Support more general iterables as return values from tasks, which may
        # not be len()-able.  If we can get a length, then we can sanity check
        # the number of output names given against the number of output values
        # produced by the task, and produce a warning if they don't match.
        try:
            num_outputs = len(new_outputs)
        except TypeError:
            num_outputs = None

        num_output_names = len(new_output_names)

        if num_outputs is not None and num_outputs != num_output_names:
            log.warning(
                'Warning: different numbers of outputs and output names for'
                ' step "%s": %d != %d',
                step_name, num_outputs, num_output_names
            )

        for output_name, output_value in zip(new_output_names, new_outputs):
            step_outputs[step_name][output_name] = output_value


def _resolve_global_parameters(
    global_parameter_spec: Union[list[str], Mapping[str, Any]],
    global_parameters: MutableMapping[str, Any]
) -> None:
    """
    Build a complete set of global parameters from the specification given in
    the experiment description and the parameter names and values given from an
    external source.

    This will update global_parameters rather than creating and returning a new
    mapping.  Entries are added for params which were missing and for which
    defaults were given in the description.  Any params given which were not
    defined in the description are removed from the mapping.  Extraneous
    parameters are not considered an error.  Any parameters defined in the
    description for which a value can't be obtained, will produce an error.

    :param global_parameter_spec: The global parameter spec from the experiment
        description
    :param global_parameters: A mapping from parameter name to value,
        representing global parameters given from some external source, e.g. on
        a commandline.
    """

    log = _get_logger()

    missing_parameters = []

    if isinstance(global_parameter_spec, list):
        # Global parameter spec was given as a list of names.  Semantics for
        # this style: all parameters are required, none are defaulted.
        for param_name in global_parameter_spec:
            if param_name not in global_parameters:
                missing_parameters.append(param_name)

        extra_parameters = global_parameters.keys() \
            - set(global_parameter_spec)

    else:
        # Global parameter spec is a dict/mapping.  Semantics for this style
        # are that all parameters are required; some may be defaulted.
        for param_name, spec_value in global_parameter_spec.items():
            if param_name not in global_parameters:
                if isinstance(spec_value, dict):
                    global_parameters[param_name] = spec_value["default"]
                elif spec_value is not None:
                    global_parameters[param_name] = spec_value
                else:
                    missing_parameters.append(param_name)

        extra_parameters = global_parameters.keys() \
            - global_parameter_spec.keys()

    if missing_parameters:
        raise MissingGlobalParametersError(missing_parameters)

    if extra_parameters:
        # This doesn't need to be a showstopper error I think.
        log.warning(
            "Some global parameters were unused: %s",
            ", ".join(extra_parameters)
        )

        # Maybe should also remove extras from the mapping?
        for param_name in extra_parameters:
            del global_parameters[param_name]


def _get_pyplugs_coords(task_plugin: str) -> list[str]:
    """
    Split a fully qualified task plugin to the three parts required as
    identifying coordinates by pyplugs.  The coordinates are:

        <package> <module> <function name>

    The task plugin is a dot-delimited string with at least two components.
    The last two components map to <module> and <function name>; everything to
    their left comprises the <package> part.  If there are only two components
    in the plugin, the package will default to the empty string.  This keeps
    with how pyplugs registers plugins.  For example:

        a.b => "" a b
        a.b.c => a b c
        a.b.c.d => a.b c d
        a.b.c.d.e => a.b.c d e

        etc...

    :param task_plugin: The dotted plugin string from the declarative
        experiment description
    :return: A length-3 list of pyplugs coordinates
    """
    coords = task_plugin.rsplit(".", 2)

    if len(coords) < 2:
        raise IllegalPluginNameError(task_plugin)

    elif len(coords) == 2:
        coords.insert(0, "")

    return coords


def _run_step(
    step: Mapping[str, Any],
    task_plugin_id: str,
    global_parameters: Mapping[str, Any],
    step_outputs: Mapping[str, Mapping[str, Any]]
) -> Any:
    """
    Run one step of a task graph.

    :param step: The step description
    :param task_plugin_id: The task plugin to call, in a composed dotted
        string form with all the parts needed by pyplugs, e.g. "a.b.c.d"
    :param global_parameters: The global parameters in use for this run, as a
        mapping from parameter name to value
    :param step_outputs: The step outputs we have thus far.  This is a nested
        mapping: step name => output name => output value.
    :return: The step output (i.e. whatever the task plugin returned)
    """

    log = _get_logger()

    # Make a shallow-copy without "dependencies", as it is not relevant to
    # finding task plugin arguments.  Removing the property means subsequent
    # code won't have to deal with it.  (A shallow copy avoids modifying the
    # caller's structure.)
    step = dict(step)
    step.pop("dependencies", None)

    if "task" in step:
        arg_specs = step
    else:
        _, arg_specs = next(iter(step.items()))

    arg_values, kwarg_values = _arg_specs_to_args(
        arg_specs, global_parameters, step_outputs
    )

    if arg_values:
        log.debug("args: %s", arg_values)
    if kwarg_values:
        log.debug("kwargs: %s", kwarg_values)

    package_name, module_name, func_name = _get_pyplugs_coords(task_plugin_id)

    output = dioptra.pyplugs.call(
        package_name, module_name, func_name, *arg_values, **kwarg_values
    )

    return output


def _run_experiment(
    experiment_desc: Mapping[str, Any],
    global_parameters: MutableMapping[str, Any]
) -> None:
    """
    Run an experiment via a declarative experiment description.

    :param experiment_desc: The experiment description, as parsed YAML or
        equivalent
    :param global_parameters: External parameter values to use in the
        experiment, as a dict
    """

    log = _get_logger()

    global_parameter_spec = experiment_desc.get("parameters", [])
    tasks = experiment_desc["tasks"]
    graph = experiment_desc["graph"]

    _resolve_global_parameters(global_parameter_spec, global_parameters)

    if log.isEnabledFor(logging.DEBUG):
        props_values = "\n  ".join(
            param_name + ": " + str(param_value)
            for param_name, param_value in global_parameters.items()
        )
        log.debug("Global parameters:\n  %s", props_values)

    step_outputs: MutableMapping[str, MutableMapping[str, Any]] \
        = collections.defaultdict(dict)

    step_order = util.get_sorted_steps(graph)

    log.debug("Step order:\n  %s", "\n  ".join(step_order))

    for step_name in step_order:

        try:
            log.info("Running step: %s", step_name)

            step = graph[step_name]

            task_plugin_short_name = util.step_get_plugin_short_name(step)
            if not task_plugin_short_name:
                raise MissingTaskPluginNameError(step_name)

            task_def = tasks.get(task_plugin_short_name)
            if not task_def:
                raise TaskPluginNotFoundError(
                    task_plugin_short_name, step_name
                )

            task_plugin_id = task_def["plugin"]

            output = _run_step(
                step, task_plugin_id, global_parameters, step_outputs
            )

            output_names = task_def.get("outputs")
            if output_names:
                _update_output_map(
                    step_outputs, step_name, output_names, output
                )
                log.debug('Output(s): %s', str(step_outputs[step_name]))

            # else: should I warn if there was an output from the task but no
            # output_names were given?

        except StepError as e:
            # Fill in useful contextual info on the error if necessary.
            if not e.context_step_name:
                e.context_step_name = step_name
            raise


def run_experiment(
    experiment_desc: Mapping[str, Any],
    global_parameters: MutableMapping[str, Any],
    mlflow_run: Any = True
):
    """
    Run an experiment via a declarative experiment description.

    :param experiment_desc: The experiment description, as parsed YAML or
        equivalent
    :param global_parameters: External parameter values to use in the
        experiment, as a dict
    :param mlflow_run: Whether and how to use an MLflow run.  If falsey, don't
        use a run.  If truthy and this parameter is a string, treat it as a
        run ID, and resume that run.  If truthy but not a string (e.g. True),
        start a new run.
    """

    # Establish mlflow contextual things first, if needed
    if mlflow_run:
        if isinstance(mlflow_run, str):
            mlflow.start_run(run_id=mlflow_run)
        else:
            mlflow.start_run()

    try:
        _run_experiment(experiment_desc, global_parameters)

        if mlflow_run:
            mlflow.end_run()

    except Exception:
        if mlflow_run:
            mlflow.end_run("FAILED")

        raise
