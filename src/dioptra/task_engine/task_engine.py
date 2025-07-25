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
import json
import logging
from collections.abc import Iterable, Mapping, MutableMapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any, NotRequired, Type, TypedDict, Union, cast

import dioptra.pyplugs
from dioptra.sdk.api.artifact import ArtifactTaskInterface
from dioptra.sdk.exceptions.task_engine import (
    ArtifactOutputNotFoundError,
    IllegalOutputReferenceError,
    IllegalPluginNameError,
    MissingGlobalParametersError,
    MissingTaskPluginNameError,
    NonIterableTaskOutputError,
    OutputNotFoundError,
    StepError,
    TaskPluginNotFoundError,
    UnresolvableReferenceError,
)
from dioptra.sdk.utilities.contexts import import_temp, sys_path_dirs
from dioptra.task_engine import util


class ArtifactTaskEntry(TypedDict):
    task: Type[ArtifactTaskInterface]
    plugin_snapshot_id: int
    task_id: int


class ArtifactOutputEntry(TypedDict):
    name: str
    task_plugin_snapshot_id: int
    task_id: int
    path: str


class ArtifactTaskNode(TypedDict):
    name: str
    args: NotRequired[dict[str, Any]]


class ArtifactNode(TypedDict):
    contents: str
    task: ArtifactTaskNode
    type: str


def _get_logger() -> logging.Logger:
    """
    Get a logger to use for functions in this module.

    Returns:
        The logger
    """
    return logging.getLogger(__name__)


class EngineContext:
    def __init__(
        self,
        experiment_desc: Mapping[str, Any],
        global_parameters: MutableMapping[str, Any],
        artifact_parameters: MutableMapping[str, Any],
        artifact_tasks: dict[str, ArtifactTaskEntry],
    ):
        log = _get_logger()

        self.global_parameters = global_parameters
        self.global_parameter_spec = experiment_desc.get("parameters", {})

        # assume this correct and has already been validated
        self.artifact_parameters = artifact_parameters

        self.tasks: dict[str, Any] = experiment_desc["tasks"]
        self.graph: dict[str, Any] = experiment_desc["graph"]
        # artifact_outputs could be None
        self.artifacts: dict[str, ArtifactNode] | None = experiment_desc.get(
            "artifact_outputs"
        )

        self.artifact_tasks: dict[str, ArtifactTaskEntry] = artifact_tasks

        _resolve_global_parameters(self.global_parameter_spec, self.global_parameters)

        if log.isEnabledFor(logging.DEBUG):
            props_values = "\n  ".join(
                param_name + ": " + str(param_value)
                for param_name, param_value in global_parameters.items()
            )
            log.debug("Global parameters:\n  %s", props_values)

        self.step_outputs: MutableMapping[str, MutableMapping[str, Any]] = (
            collections.defaultdict(dict)
        )

    def get_task_definition(
        self, short_name: str
    ) -> tuple[str, Mapping[str, str] | Sequence[Mapping[str, str]] | None] | None:
        task_def = self.tasks.get(short_name)
        if task_def is None:
            return None
        return (task_def["plugin"], task_def.get("outputs"))

    def get_step(self, step_name: str) -> dict[str, Any]:
        return cast(dict[str, Any], self.graph[step_name])

    def get_ordered_steps(self) -> Iterable[str]:
        return util.get_sorted_steps(self.graph)

    def get_artifacts(self) -> dict[str, ArtifactNode] | None:
        return self.artifacts

    def register_outputs(
        self,
        step_name: str,
        output_defs: Union[Mapping[str, str], Sequence[Mapping[str, str]]],
        output: Any,
    ):
        log = _get_logger()

        _update_output_map(self.step_outputs, step_name, output_defs, output)
        log.debug("Output(s): %s", str(self.step_outputs[step_name]))

    def resolve_reference(self, reference: str) -> Any:
        """
        Resolve a reference to a task output, global parameter, or artifact parameter.

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
            # Must be an <step>.<output> or <artifact>.<output> formatted reference
            reference_name, output_name = reference.split(".", 1)

            step_output = self.step_outputs.get(reference_name)
            if step_output is not None:
                if output_name not in step_output:
                    raise OutputNotFoundError(reference_name, output_name)

                value = step_output[output_name]
            else:
                parameter_outputs = self.artifact_parameters.get(reference_name)
                if not parameter_outputs:
                    raise UnresolvableReferenceError(reference_name)

                if output_name not in parameter_outputs:
                    raise ArtifactOutputNotFoundError(reference_name, output_name)
                value = parameter_outputs[output_name]

        else:
            # A bare name may refer to either a global parameter, the only output of a
            # step or an artifact.  Assume prior validation ensured the name is unique.
            if reference in self.global_parameters:
                value = self.global_parameters[reference]
            elif reference in self.step_outputs:
                outputs = self.step_outputs[reference]
                if len(outputs) != 1:
                    raise IllegalOutputReferenceError(reference)
                value = next(iter(outputs.values()))
            elif reference in self.artifact_parameters:
                value = self.artifact_parameters[reference]
                if len(value) != 1:
                    raise IllegalOutputReferenceError(reference)
                value = next(iter(value.values()))

            else:
                raise UnresolvableReferenceError(reference)

        return value

    def find_artifact_task(self, task_name: str) -> ArtifactTaskEntry:
        return self.artifact_tasks[task_name]


def _resolve_task_parameter_value(
    arg_spec: Any,
    context: EngineContext,
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
            arg_value = context.resolve_reference(arg_spec[1:])

        elif arg_spec.startswith("$$"):
            # "escaped" dollar sign: replace only the initial "$$" with "$"
            arg_value = arg_spec[1:]

        else:
            arg_value = arg_spec

    elif isinstance(arg_spec, dict):
        arg_value = {
            key: _resolve_task_parameter_value(value, context)
            for key, value in arg_spec.items()
        }

    elif isinstance(arg_spec, list):
        arg_value = [
            _resolve_task_parameter_value(sub_val, context) for sub_val in arg_spec
        ]

    else:
        arg_value = arg_spec

    return arg_value


def _positional_specs_to_args(
    arg_specs: Iterable[Any],
    context: EngineContext,
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
        _resolve_task_parameter_value(arg_spec, context) for arg_spec in arg_specs
    ]

    return arg_values


def _kwarg_specs_to_kwargs(
    kwarg_specs: Mapping[str, Any],
    context: EngineContext,
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
        kwarg_name: _resolve_task_parameter_value(kwarg_value, context)
        for kwarg_name, kwarg_value in kwarg_specs.items()
    }

    return kwarg_values


def _get_invocation_args(
    step: Mapping[str, Any],
    context: EngineContext,
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
    arg_values = _positional_specs_to_args(pos_arg_specs, context)

    kwarg_values = _kwarg_specs_to_kwargs(kwarg_specs, context)

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
    step: Mapping[str, Any], task_plugin_id: str, context: EngineContext
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

    arg_values, kwarg_values = _get_invocation_args(step, context)

    if arg_values:
        log.debug("args: %s", arg_values)
    if kwarg_values:
        log.debug("kwargs: %s", kwarg_values)

    package_name, module_name, func_name = _get_pyplugs_coords(task_plugin_id)

    output = dioptra.pyplugs.call(
        package_name, module_name, func_name, *arg_values, **kwarg_values
    )

    return output


def _load_artifact_parameters(
    deserialize_dir: Path,
    artifacts_dir: Path,
    artifact_parameters: MutableMapping[str, Any],
) -> dict[str, Any]:
    log = _get_logger()

    result: dict[str, dict[str, Any]] = {}
    # go through and load up each artifact
    for name, info in artifact_parameters.items():
        artifact_dir = f"{info['artifact_id']}_{info['artifact_snapshot_id']}"
        task_info = info["artifact_task"]
        plugin_name = f"{task_info['plugin_id']}_{task_info['plugin_snapshot_id']}"
        outputs = task_info["outputs"]
        file_name = Path(task_info["file_name"])
        with import_temp(
            f"{plugin_name}.{file_name.stem}", deserialize_dir
        ) as artifact_task:
            task = cast(
                ArtifactTaskInterface | None,
                getattr(artifact_task, task_info["task_name"], None),
            )
            if task is None:
                log.error(
                    f"Failed to locate artifact task: {task_info['task_name']} in "
                    f"plugin: {plugin_name} for artifact parameter: {name}"
                )
                exit(1)
            if info["is_dir"]:
                value = task.deserialize(working_dir=artifacts_dir, path=artifact_dir)
            else:
                uri_name = PurePosixPath(info["artifact_uri"]).name
                value = value = task.deserialize(
                    working_dir=artifacts_dir / artifact_dir, path=uri_name
                )
            result[name] = {}
            num_expected_outputs = len(outputs)
            if num_expected_outputs == 1:
                result[name][outputs[0]["name"]] = value
            else:
                # Task plugin return value must be iterable.
                if not util.is_iterable(value):
                    raise NonIterableTaskOutputError(value, f"artifacts.{name}")

                # Support more general iterables as return values from tasks, which may
                # not be len()-able.  If we can get a length, then we can sanity check
                # the number of output names given against the number of output values
                # produced by the task, and produce a warning if they don't match.
                try:
                    num_outputs = len(value)
                except TypeError:
                    num_outputs = None

                if num_outputs is not None and num_outputs != num_expected_outputs:
                    log.warning(
                        "Different numbers of outputs and expected outputs for "
                        'artifact parameter "%s": %d != %d',  # noqa: B950
                        name,
                        num_outputs,
                        num_expected_outputs,
                    )
                for param, output_value in zip(outputs, value):
                    result[name][param["name"]] = output_value

    return result


def _run_steps(context: EngineContext) -> None:
    log = _get_logger()
    step_order = context.get_ordered_steps()
    log.debug("Step order:\n  %s", "\n  ".join(step_order))

    for step_name in step_order:
        try:
            log.info("Running step: %s", step_name)

            step = context.get_step(step_name)

            task_plugin_short_name = util.step_get_plugin_short_name(step)
            if not task_plugin_short_name:
                raise MissingTaskPluginNameError(step_name)

            task_def = context.get_task_definition(task_plugin_short_name)
            if not task_def:
                raise TaskPluginNotFoundError(task_plugin_short_name, step_name)

            task_plugin_id, output_defs = task_def

            output = _run_step(step, task_plugin_id, context)
            if output_defs:
                context.register_outputs(step_name, output_defs, output)

            # else: should I warn if there was an output from the task but no
            # output_names were given?

        except StepError as e:
            # Fill in useful contextual info on the error if necessary.
            if not e.context_step_name:
                e.context_step_name = step_name
            raise


def _handle_artifacts(
    artifacts: dict[str, ArtifactNode],
    context: EngineContext,
) -> list[ArtifactOutputEntry]:
    result: list[ArtifactOutputEntry] = []
    for name, artifact in artifacts.items():
        contents = _resolve_task_parameter_value(artifact["contents"], context)
        task_name = artifact["task"]["name"]
        # search through plug-ins to find the correct artifact task based on the name
        entry = context.find_artifact_task(task_name)
        args: dict[str, Any] = {}
        if "args" in artifact["task"]:
            args = artifact["task"]["args"]

        path = entry["task"].serialize(Path.cwd(), name, contents, **args)

        result.append(
            ArtifactOutputEntry(
                name=name,
                task_plugin_snapshot_id=entry["plugin_snapshot_id"],
                task_id=entry["task_id"],
                path=path.as_posix(),
            )
        )

    return result


def run_experiment(
    experiment_desc: Mapping[str, Any],
    global_parameters: MutableMapping[str, Any],
    artifact_parameters: MutableMapping[str, Any],
    artifact_tasks: dict[str, ArtifactTaskEntry],
    artifacts_dir: Path,
    plugins_dir: Path,
    serialize_dir: Path,
    deserialize_dir: Path,
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

    loaded_artifacts_params = _load_artifact_parameters(
        artifacts_dir=artifacts_dir,
        deserialize_dir=deserialize_dir,
        artifact_parameters=artifact_parameters,
    )

    context = EngineContext(
        experiment_desc=experiment_desc,
        global_parameters=global_parameters,
        artifact_parameters=loaded_artifacts_params,
        artifact_tasks=artifact_tasks,
    )

    # add the plug-ins directory and cycle through the steps
    with sys_path_dirs(dirs=(str(plugins_dir),)):
        _run_steps(context)

    # handle artifacts
    with sys_path_dirs(dirs=(str(serialize_dir),)):
        artifacts = context.get_artifacts()
        if artifacts is not None:
            artifacts_result = _handle_artifacts(artifacts, context)

            # output the artifacts.json file
            with open(".dioptra/artifacts.json", "w") as file:
                json.dump({"artifacts": artifacts_result}, file)

            log.debug("Saved artifacts.json file")
