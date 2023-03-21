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
import sys

import yaml

import dioptra.task_engine.validation


def parse_args() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser(
        description="""
        Simple commandline tool to statically validate a declarative
        experiment description file.
        """,
        epilog="""
        Exit status is 0 if no issues were found; 1 if there were issues; 2
        if an exception occurs.
        """,
    )

    arg_parser.add_argument(
        "file",
        help="""The file to validate""",
        type=argparse.FileType("r", encoding="utf-8"),
    )

    arg_parser.add_argument(
        "-q",
        "--quiet",
        help="""Be quiet.  If given twice, silence stack traces too.""",
        action="count",
        default=0,
    )

    return arg_parser.parse_args()


def main() -> int:
    exit_status = 0
    args = parse_args()

    try:
        experiment_desc = yaml.safe_load(args.file)
        issues = dioptra.task_engine.validation.validate(experiment_desc)
        if issues:
            exit_status = 1
            if args.quiet < 1:
                print("Issues:")
                print()
                for i, issue in enumerate(issues):
                    print(i + 1, ". ", issue, sep="")
                    print()

        else:
            if args.quiet < 1:
                print("No issues!")

    except Exception:
        exit_status = 2
        if args.quiet < 2:
            sys.excepthook(*sys.exc_info())

    return exit_status


if __name__ == "__main__":
    sys.exit(main())
