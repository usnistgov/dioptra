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
