import argparse
import logging
import logging.config
from collections.abc import Iterable
from typing import Any, Union

import yaml

import dioptra.task_engine.task_engine


def _parse_args() -> argparse.Namespace:
    """
    Set up and parse commandline parameters.
    """
    arg_parser = argparse.ArgumentParser(
        description="Read/process declarative experiment description",
        epilog="""
        By default, if neither --no-run nor --run-id are given, an experiment
        runs in the context of a new MLflow run.
        """
    )

    arg_parser.add_argument(
        "file",
        type=argparse.FileType(mode="r", encoding="utf-8"),
        help="The declarative experiment file to read"
    )

    arg_parser.add_argument(
        "-P",
        help="""
        Assign values to task graph global parameters.  Values must be of the
        form <name>=<value>.  This option can be repeated.
        """,
        action="append",
        metavar="name=value"
    )

    arg_parser.add_argument(
        "-l", "--log-level",
        help='''
        Set the logging level.  "all" is a special setting which causes logging
        from all modules to display at the debug level, in addition to this
        application.  This can result in a lot of logging noise.
        Default: %(default)s
        ''',
        choices=["all", "debug", "info", "warning", "error", "critical"],
        default="info"
    )

    run_group = arg_parser.add_mutually_exclusive_group()

    run_group.add_argument(
        "--run-id",
        help="""
        Resume the given MLflow run, for this experiment.
        """
    )

    run_group.add_argument(
        "--no-run",
        help="""
        Do not run the experiment in the context of a MLflow run.
        """,
        # This is a "negative" option, i.e. its presence turns something off,
        # but I'd prefer to keep it positive in the resulting args object.
        dest="use_run",
        action="store_false"
    )

    return arg_parser.parse_args()


def _setup_logging(log_level: Union[int, str] = logging.INFO) -> None:
    """
    Set up logging.

    :param log_level: The logging level to use.  May be one of the integer log
        level constants or names recognized by the logging module, or "all".
    """

    if isinstance(log_level, str):
        log_level = log_level.upper()

    config = {
        "version": 1,

        "formatters": {
            "fmt": {
                # Uniform width, so we get nice alignment, with enough room for
                # the word "critical".
                "format": "[%(levelname)8s] %(message)s"
            }
        },

        "handlers": {
            "stream": {
                "class": "logging.StreamHandler",
                "formatter": "fmt"
            }
        },

        "disable_existing_loggers": False
    }

    logger_config: dict[str, Any] = {
        "handlers": ["stream"]
    }

    # Set the logging config on the root logger if "ALL", else just on
    # the task_graph module.
    if log_level == "ALL":
        logger_config["level"] = "DEBUG"
        config["root"] = logger_config
    else:
        # TODO: when this code is integrated into dioptra, update to reflect
        # the final location of the task_engine module!
        logger_config["level"] = log_level
        config["loggers"] = {
            "dioptra.task_engine": logger_config
        }

    logging.config.dictConfig(config)


def _cmdline_params_to_map(params: Iterable[str]) -> dict[str, str]:
    """
    Convert global parameters given on the commandline in <name>=<value>
    format, into a mapping from name to value.  Values are run through a YAML
    evaluation so that there is more flexibility in terms of value types, than
    just using strings.  If an equals sign and value are missing (e.g. it is
    just <name>), this is treated the same as <name>=true.  If the format is
    =<value> this is an error: a parameter name is required.  If the format is
    <name>= this is not an error: the value is the empty string.

    :param params: The commandline parameters defining global experiment
        parameters, as collected by argparse.
    :return: A mapping from name (string) to value (some python type)
    """
    param_value: Any
    param_map = {}

    if params:
        for param in params:
            equals_idx = param.find("=")

            if equals_idx == 0:
                raise ValueError(
                    "Global parameter names must not be empty: " + param
                )

            elif equals_idx < 0:
                # No equals sign: treat this as setting a "true" value.
                param_name = param
                param_value = True

            else:
                param_name = param[:equals_idx]
                param_value = param[equals_idx+1:]

                # run a yaml evaluation to try to convert the value to some
                # Python type which is more specialized than a string.
                param_value = yaml.safe_load(param_value)

            param_map[param_name] = param_value

    return param_map


def main() -> None:
    args = _parse_args()
    _setup_logging(args.log_level)

    experiment_desc = yaml.safe_load(args.file)
    global_parameters = _cmdline_params_to_map(args.P)

    mlflow_run = args.use_run
    if mlflow_run and args.run_id:
        mlflow_run = args.run_id

    dioptra.task_engine.task_engine.run_experiment(
        experiment_desc, global_parameters, mlflow_run
    )


if __name__ == "__main__":
    main()
