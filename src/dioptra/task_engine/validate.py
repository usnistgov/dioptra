import argparse

import yaml

import dioptra.task_engine.validation


def parse_args() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser(
        description="""
        Simple commandline tool to statically validate a declarative
        experiment description file.
        """
    )

    arg_parser.add_argument(
        "file",
        help="""The file to validate""",
        type=argparse.FileType("r", encoding="utf-8"),
    )

    return arg_parser.parse_args()


def main() -> None:

    args = parse_args()

    experiment_desc = yaml.safe_load(args.file)
    issues = dioptra.task_engine.validation.validate(experiment_desc)
    if issues:
        print("Issues:")
        print()
        for i, issue in enumerate(issues):
            print(i + 1, ". ", issue, sep="")
            print()

    else:
        print("No issues!")


if __name__ == "__main__":
    main()
