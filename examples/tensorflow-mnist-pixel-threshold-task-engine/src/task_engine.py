import collections
import itertools
import logging
from collections.abc import (
    Container,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Sequence,
)
from typing import Any, Union

import mlflow

import dioptra.pyplugs


def _get_logger() -> logging.Logger:
    """
    Get a logger to use for functions in this module.

    :return: The logger
    """
    return logging.getLogger(__name__)


def _is_iterable(value: Any) -> bool:
    """
    Determine whether the given value is iterable.  Works by attempting to
    get an iterator from it.

    :param value: The value to check
    :return: True if the value is iterable; False if not
    """
    try:
        iter(value)
    except TypeError:
        result = False
    else:
        result = True

    return result


def _is_reference(value: str) -> bool:
    """
    Determine whether the given string, as may be found in a task invocation
    specification, is syntactically a reference.  References begin with a
    dollar sign and are followed by some non-dollar-sign characters, e.g.
    "$foo".  A dollar sign may be escaped by doubling it.  So "$$foo" is not a
    reference, but just means the string "$foo".  If there are no
    non-dollar-sign characters, it is not a reference, e.g. "$", "$$", etc.
    This function does not try to actually resolve the reference, so if the
    value is a reference, this function does not guarantee it is valid.

    :param value: The string to check
    :return: True if the given string is a reference; False if not
    """

    return value != "$" \
        and value.startswith("$") \
        and not value.startswith("$$")


def _get_references(input_: Any) -> Iterator[str]:
    """
    Search for references within a task invocation specification, and generate
    the names.  This just makes the reference determination syntactically, and
    doesn't attempt to resolve any reference.

    :param input_: The arg spec structure to search for references
    """

    if isinstance(input_, str):

        if _is_reference(input_):
            yield input_[1:]  # drop the leading "$"

    elif isinstance(input_, dict):
        if "task" in input_:
            args = input_.get("args")
            kwargs = input_.get("kwargs")
            if args:
                yield from _get_references(args)
            if kwargs:
                yield from _get_references(kwargs.values())
        else:
            yield from _get_references(input_.values())

    elif _is_iterable(input_):
        for elt in input_:
            yield from _get_references(elt)


def _get_step_references(
    input_: Any,
    step_names: Container[str]
) -> Iterator[str]:
    """
    Generate step names from references in the input which refer to steps.

    :param input_: The arg spec structure to search for references to steps
    :param step_names: A container with all of the step names.  This allows us
        to recognize a step name when we see one.
    """
    # Note: erroneous references will not be caught here (i.e. those which
    # don't refer to either a step name or a global parameter).  Those errors
    # will be caught later, when we actually need to resolve the references.
    for ref_name in _get_references(input_):
        dot_idx = ref_name.find(".")
        if dot_idx >= 0:
            step_name = ref_name[:dot_idx]
        else:
            step_name = ref_name

        if step_name in step_names:
            yield step_name


def _step_dfs(
    step_graph: Mapping[str, Any],
    curr_step_name: str,
    visited_steps: MutableSet[str],
    search_path: MutableSequence[str]
) -> list[str]:
    """
    Perform depth-first search through the task graph, to produce a total order
    over step names which is compatible with the steps' dependencies.

    :param step_graph: The task graph data from the experiment description.
        This maps step names to task invocations.
    :param curr_step_name: The start node of the DFS (since the algorithm is
        recursive, this actually tracks the "current node" through the
        recursive calls).
    :param visited_steps: Set containing steps which have already been visited,
        to avoid visiting any step more than once.  Steps are added to this
        set as the search proceeds.
    :param search_path: A list (acting as a stack) of step names on the current
        search path, used to detect cycles.  Steps are pushed and popped from
        this list as the search proceeds.
    :return: A list of the steps reachable from the start, in topological
        sorted order
    """

    if curr_step_name in search_path:
        raise ValueError("Cycle detected!")

    elif curr_step_name not in step_graph:
        raise ValueError("Step not found: " + curr_step_name)

    sorted_steps = []

    if curr_step_name not in visited_steps:

        curr_step = step_graph[curr_step_name]
        visited_steps.add(curr_step_name)
        search_path.append(curr_step_name)

        # All dependencies include those implied by declared task inputs,
        # and those explicitly listed as dependencies (via the "dependencies"
        # key).

        implicit_deps = _get_step_references(curr_step, step_graph.keys())

        explicit_deps = curr_step.get("dependencies", [])
        if isinstance(explicit_deps, str):
            explicit_deps = [explicit_deps]

        all_dependencies = itertools.chain(
            implicit_deps,
            explicit_deps
        )

        for next_step_name in all_dependencies:
            sub_sorted = _step_dfs(
                step_graph, next_step_name, visited_steps, search_path
            )
            sorted_steps.extend(sub_sorted)

        search_path.pop()
        sorted_steps.append(curr_step_name)

    return sorted_steps


def _get_sorted_steps(step_graph: Mapping[str, Any]) -> list[str]:
    """
    Topological sorts the step graph to obtain a sequential execution order.

    :param step_graph: The task graph data from the experiment description.
        This maps step names to task invocations.
    :return: A list of all step names in the graph, in topological sorted order
        according to their dependencies
    """

    sorted_steps = []
    visited_steps: MutableSet[str] = set()
    for step in step_graph:
        sub_sorted = _step_dfs(step_graph, step, visited_steps, [])
        sorted_steps.extend(sub_sorted)

    return sorted_steps


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
            raise Exception("Step not found: " + step_name)

        if output_name not in step_output:
            raise Exception(
                "Unrecognized output of step "
                + step_name + ": " + output_name
            )

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
                raise Exception(
                    "A reference to a step which does not have exactly"
                    " one output must include an output name as"
                    " <step>.<output>: " + reference
                )
            value = next(iter(outputs.values()))
        else:
            raise Exception("Unresolvable reference: " + reference)

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

        if _is_reference(arg_spec):
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
        if not _is_iterable(new_outputs):
            raise TypeError(
                'Task output name(s) for step "{}" were given as a list,'
                ' but the task plugin did not return an iterable value: {}'
                .format(step_name, type(new_outputs))
            )

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
        raise Exception(
            "Missing values for global parameters: "
            + ", ".join(missing_parameters)
        )

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
    their left comprises the package> part.  If there are only two components
    in the plugin, the package will default to the empty string.  This keeps
    with how pyplugs registers plugins.  For example:

        a.b => "" a b
        a.b.c => a b c
        a.b.c.d => a.b c d
        a.b.c.d.e => a.b.c d e

        etc...

    :param task_plugin:
    :return: A length-3 list of pyplugs coordinates
    """
    coords = task_plugin.rsplit(".", 2)

    if len(coords) < 2:
        raise Exception(
            "A task plugin must be a dot-delimited string of at least two"
            " components: " + task_plugin
        )

    elif len(coords) == 2:
        coords.insert(0, "")

    return coords


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

    step_order = _get_sorted_steps(graph)

    log.debug("Step order:\n  %s", "\n  ".join(step_order))

    for step_name in step_order:

        log.info("Running step: %s", step_name)

        step = graph[step_name]

        if "task" in step:
            task_short_name = step["task"]
            arg_specs = step
        else:
            task_short_name, arg_specs = next(iter(step.items()))

        arg_values, kwarg_values = _arg_specs_to_args(
            arg_specs, global_parameters, step_outputs
        )

        if arg_values:
            log.debug('Step "%s" args: %s', step_name, arg_values)
        if kwarg_values:
            log.debug('Step "%s" kwargs: %s', step_name, kwarg_values)

        task_def = tasks[task_short_name]
        task_plugin = task_def["plugin"]

        package_name, module_name, func_name = _get_pyplugs_coords(task_plugin)

        try:
            
            output = dioptra.pyplugs.call(
                package_name, module_name, func_name,
                *arg_values, **kwarg_values
            )
        except TypeError as e:
            # This is nasty, but inside pyplugs, importlib raises an exception
            # of a very generic type (TypeError) if you give it an empty
            # package name, and it has to import the module (because the tasks
            # aren't already registered).  I don't feel like I can safely catch
            # all TypeErrors and report this more useful message for this
            # particular pyplugs issue, since it would not make sense if a
            # TypeError were thrown for a different reason.  So I need to
            # distinguish a pyplugs TypeError (really, an importlib error) from
            # a TypeError which may come from the called task.  I do that by
            # checking the contents of the error message.  Ugh.  Dioptra
            # plugins will probably all be in packages, so this will probably
            # never be an issue in practice.
            if "is required to perform a relative import" in str(e):
                raise Exception(
                    "Pyplugs' auto-registration requires a Python package."
                    "  You must either manually register plugins (e.g. by"
                    " manually importing their module(s)) before running this"
                    " experiment, or move the file with tasks into a"
                    " subdirectory which is a package, and update your"
                    " experiment to reference task plugins via the package."
                ) from e

            else:
                raise

        output_names = task_def.get("outputs")
        if output_names:
            _update_output_map(step_outputs, step_name, output_names, output)
            log.debug(
                'Step "%s" output(s): %s',
                step_name, str(step_outputs[step_name])
            )

        # else: should I warn if there was an output from the task but no
        # output_names were given?


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