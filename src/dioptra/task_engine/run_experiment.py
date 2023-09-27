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
    )

    arg_parser.add_argument(
        "file",
        type=argparse.FileType(mode="r", encoding="utf-8"),
        help="The declarative experiment file to read",
    )

    arg_parser.add_argument(
        "-P",
        help="""
        Assign values to task graph global parameters.  Values must be of the
        form <name>=<value>.  This option can be repeated.
        """,
        action="append",
        metavar="name=value",
    )

    arg_parser.add_argument(
        "-l",
        "--log-level",
        help="""
        Set the logging level.  "all" is a special setting which causes logging
        from all modules to display at the debug level, in addition to this
        application.  This can result in a lot of logging noise.
        Default: %(default)s
        """,
        choices=["all", "debug", "info", "warning", "error", "critical"],
        default="info",
    )

    return arg_parser.parse_args()


def _setup_logging(log_level: Union[int, str] = logging.INFO) -> None:
    """
    Set up logging.

    Args:
        log_level: The logging level to use.  May be one of the integer log
            level constants or names recognized by the logging module, or
            "all".
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
        "handlers": {"stream": {"class": "logging.StreamHandler", "formatter": "fmt"}},
        "disable_existing_loggers": False,
    }

    logger_config: dict[str, Any] = {"handlers": ["stream"]}

    # Set the logging config on the root logger if "ALL", else just on
    # the task_graph module.
    if log_level == "ALL":
        logger_config["level"] = "DEBUG"
        config["root"] = logger_config
    else:
        logger_config["level"] = log_level
        config["loggers"] = {"dioptra.task_engine": logger_config}

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

    Args:
        params: The commandline parameters defining global experiment
            parameters, as collected by argparse.

    Returns:
        A mapping from name (string) to value (some python type)
    """
    param_value: Any
    param_map = {}

    if params:
        for param in params:
            equals_idx = param.find("=")

            if equals_idx == 0:
                raise ValueError("Global parameter names must not be empty: " + param)

            elif equals_idx < 0:
                # No equals sign: treat this as setting a "true" value.
                param_name = param
                param_value = True

            else:
                param_name = param[:equals_idx]
                param_value = param[equals_idx + 1 :]

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

    dioptra.task_engine.task_engine.run_experiment(experiment_desc, global_parameters)


if __name__ == "__main__":
    main()
