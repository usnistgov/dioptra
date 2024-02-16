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
import collections
import itertools
import logging
from collections.abc import Iterable, Mapping, MutableMapping, Sequence
from typing import Any, Union

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

    Returns:
        The logger
    """
    return logging.getLogger(__name__)


def _resolve_reference(
    reference: str,
    global_parameters: Mapping[str, Any],
    step_outputs: Mapping[str, Mapping[str, Any]],
) -> Any:
    """
    Resolve a reference to a task output or global parameter.

    Args:
        reference: The reference to resolve, without the "$" prefix
        global_parameters: The global parameters in use for this run, as a
            mapping from parameter name to value
        step_outputs: The step outputs we have thus far.  This is a nested
            mapping: step name => output name => output value.

    Returns:
        The referenced value
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
    step_outputs: Mapping[str, Mapping[str, Any]],
) -> Any:
    """
    Resolve a specification for one argument of a task invocation, to the
    actual value to be used in the invocation.

    Args:
        arg_spec: The argument specification
        global_parameters: The global parameters in use for this run, as a
            mapping from parameter name to value
        step_outputs: The step outputs we have thus far.  This is a nested
            mapping: step name => output name => output value.

    Returns:
        The value to use for the given parameter
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
            key: _resolve_task_parameter_value(value, global_parameters, step_outputs)
            for key, value in arg_spec.items()
        }

    elif isinstance(arg_spec, list):
        arg_value = [
            _resolve_task_parameter_value(sub_val, global_parameters, step_outputs)
            for sub_val in arg_spec
        ]

    else:
        arg_value = arg_spec

    return arg_value


def _positional_specs_to_args(
    arg_specs: Iterable[Any],
    global_parameters: Mapping[str, Any],
    step_outputs: Mapping[str, Mapping[str, Any]],
) -> list[Any]:
    """
    Resolve a positional parameter style invocation specification to a list
    of actual parameter values to use in the task invocation.

    Args:
        arg_specs: A list of argument specifications.
        global_parameters: The global parameters in use for this run, as a
            mapping from parameter name to value
        step_outputs: The step outputs we have thus far.  This is a nested
            mapping: step name => output name => output value.

    Returns:
        A list of values to use for the invocation
    """

    arg_values = [
        _resolve_task_parameter_value(arg_spec, global_parameters, step_outputs)
        for arg_spec in arg_specs
    ]

    return arg_values


def _kwarg_specs_to_kwargs(
    kwarg_specs: Mapping[str, Any],
    global_parameters: Mapping[str, Any],
    step_outputs: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """
    Resolve a keyword arg style invocation specification to a mapping of actual
    parameter values to use in the task invocation.

    Args:
        kwarg_specs: A mapping from keyword arg name to value specification
        global_parameters: The global parameters in use for this run, as a
            mapping from parameter name to value
        step_outputs: The step outputs we have thus far.  This is a nested
            mapping: step name => output name => output value.

    Returns:
        A mapping from parameter name to actual value to use for the
        task invocation
    """
    kwarg_values = {
        kwarg_name: _resolve_task_parameter_value(
            kwarg_value, global_parameters, step_outputs
        )
        for kwarg_name, kwarg_value in kwarg_specs.items()
    }

    return kwarg_values


def _get_invocation_args(
    step: Mapping[str, Any],
    global_parameters: Mapping[str, Any],
    step_outputs: Mapping[str, Mapping[str, Any]],
) -> tuple[list[Any], dict[str, Any]]:
    """
    Resolve a task invocation specification to all of the positional and
    keyword arg values to use in the invocation.

    Args:
        step: The step description
        global_parameters: The global parameters in use for this run, as a
            mapping from parameter name to value
        step_outputs: The step outputs we have thus far.  This is a nested
            mapping: step name => output name => output value.

    Returns:
        A 2-tuple including a list of positional values to use in the
        task invocation, followed by a mapping with keyword arg names and
        values.
    """

    pos_arg_specs, kwarg_specs = util.step_get_invocation_arg_specs(step)

    # step_get_invocation_args() is written to be graceful in the face of a
    # malformed step definition (and return nulls), but at this point I think
    # we can assume validation has already been done, as would be the normal
    # workflow, so nulls won't happen here.
    assert pos_arg_specs is not None
    assert kwarg_specs is not None

    # Assume for now that validation has completed successfully, so we always
    # have a correct step definition with arg specs?
    arg_values = _positional_specs_to_args(
        pos_arg_specs, global_parameters, step_outputs
    )

    kwarg_values = _kwarg_specs_to_kwargs(kwarg_specs, global_parameters, step_outputs)

    return arg_values, kwarg_values


def _update_output_map(
    step_outputs: MutableMapping[str, MutableMapping[str, Any]],
    step_name: str,
    output_defs: Union[Mapping[str, str], Sequence[Mapping[str, str]]],
    new_outputs: Any,
) -> None:
    """
    Update the step outputs mapping according to task metadata regarding output
    name(s), and actual task plugin return value(s).

    Args:
        step_outputs: The step outputs we have thus far.  This a is nested
            mapping: step name => output name => output value.
        step_name: The name of the step for which we have output values
        output_defs: Task metadata regarding outputs.  This may be either a
            single or list of mappings.
        new_outputs: The output(s) from the completed step
    """

    log = _get_logger()

    if isinstance(output_defs, Mapping):
        # If a single output is defined, store the task return value directly
        # under that name.
        output_name = next(iter(output_defs))
        step_outputs[step_name][output_name] = new_outputs

    else:
        # else, output_defs is a list.  Task plugin return value must
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

        num_output_names = len(output_defs)

        if num_outputs is not None and num_outputs != num_output_names:
            log.warning(
                'Different numbers of outputs and output definitions for step "%s": %d != %d',  # noqa: B950
                step_name,
                num_outputs,
                num_output_names,
            )

        output_names = itertools.chain.from_iterable(output_defs)

        for output_name, output_value in zip(output_names, new_outputs):
            step_outputs[step_name][output_name] = output_value


def _resolve_global_parameters(
    global_parameter_spec: Mapping[str, Any],
    global_parameters: MutableMapping[str, Any],
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

    Args:
        global_parameter_spec: The global parameter spec from the experiment
            description
        global_parameters: A mapping from parameter name to value, representing
            global parameters given from some external source, e.g. on a
            commandline.
    """

    log = _get_logger()

    missing_parameters = []

    for param_name, param_def in global_parameter_spec.items():
        if param_name not in global_parameters:
            if isinstance(param_def, dict):
                if "default" in param_def:
                    global_parameters[param_name] = param_def["default"]
                else:
                    missing_parameters.append(param_name)
            else:
                global_parameters[param_name] = param_def

    extra_parameters = global_parameters.keys() - global_parameter_spec.keys()

    if missing_parameters:
        raise MissingGlobalParametersError(missing_parameters)

    if extra_parameters:
        # This doesn't need to be a showstopper error I think.
        log.warning(
            "Some global parameters were unused: %s", ", ".join(extra_parameters)
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

    Args:
        task_plugin: The dotted plugin string from the declarative experiment
            description

    Returns:
        A length-3 list of pyplugs coordinates
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
    step_outputs: Mapping[str, Mapping[str, Any]],
) -> Any:
    """
    Run one step of a task graph.

    Args:
        step: The step description
        task_plugin_id: The task plugin to call, in a composed dotted
            string form with all the parts needed by pyplugs, e.g. "a.b.c.d"
        global_parameters: The global parameters in use for this run, as a
            mapping from parameter name to value
        step_outputs: The step outputs we have thus far.  This is a nested
            mapping: step name => output name => output value.

    Returns:
        The step output (i.e. whatever the task plugin returned)
    """

    log = _get_logger()

    arg_values, kwarg_values = _get_invocation_args(
        step, global_parameters, step_outputs
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


def run_experiment(
    experiment_desc: Mapping[str, Any], global_parameters: MutableMapping[str, Any]
) -> None:
    """
    Run an experiment via a declarative experiment description.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent
        global_parameters: External parameter values to use in the
            experiment, as a dict
    """

    log = _get_logger()

    global_parameter_spec = experiment_desc.get("parameters", {})
    tasks = experiment_desc["tasks"]
    graph = experiment_desc["graph"]

    _resolve_global_parameters(global_parameter_spec, global_parameters)

    if log.isEnabledFor(logging.DEBUG):
        props_values = "\n  ".join(
            param_name + ": " + str(param_value)
            for param_name, param_value in global_parameters.items()
        )
        log.debug("Global parameters:\n  %s", props_values)

    step_outputs: MutableMapping[str, MutableMapping[str, Any]] = (
        collections.defaultdict(dict)
    )

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
                raise TaskPluginNotFoundError(task_plugin_short_name, step_name)

            task_plugin_id = task_def["plugin"]

            output = _run_step(step, task_plugin_id, global_parameters, step_outputs)

            output_defs = task_def.get("outputs")
            if output_defs:
                _update_output_map(step_outputs, step_name, output_defs, output)
                log.debug("Output(s): %s", str(step_outputs[step_name]))

            # else: should I warn if there was an output from the task but no
            # output_names were given?

        except StepError as e:
            # Fill in useful contextual info on the error if necessary.
            if not e.context_step_name:
                e.context_step_name = step_name
            raise
