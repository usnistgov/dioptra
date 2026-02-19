#!/usr/bin/env python
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
"""Validate that a git tag matches the version in pyproject.toml."""

import argparse
import os
import re
import sys
import tomllib
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="Git tag to validate")
    parser.add_argument(
        "--strip-v-prefix",
        action="store_true",
        help="Strip 'v' prefix from tag before comparison",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="If set, do not set GitHub Actions outputs",
    )
    return parser.parse_args()


def get_pyproject_version(pyproject_path: Path) -> str:
    """Extract version from pyproject.toml."""
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    version = data.get("project", {}).get("version")
    if version is None:
        dynamic = data.get("project", {}).get("dynamic", [])
        if "version" in dynamic:
            print("::error::Version is dynamic; cannot validate against static tag")
            sys.exit(1)

        print("::error::No version found in pyproject.toml")
        sys.exit(1)

    return str(version)


def is_prerelease(version: str) -> bool:
    """Check if version is a pre-release (dev, alpha, beta, rc)."""
    prerelease_pattern = r"(dev|alpha|beta|rc|a|b|c)\d*"
    return bool(re.search(prerelease_pattern, version, re.IGNORECASE))


def set_output(name: str, value: str, dry_run: bool) -> None:
    """Set GitHub Actions output."""
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"{name}={value}\n")

    print(f"Output: {name}={value}")


def main() -> None:
    args = parse_args()

    if dry_run := args.dry_run:
        print("Dry run mode: outputs will not be set")

    tag = args.tag
    if args.strip_v_prefix and tag.startswith("v"):
        tag = tag[1:]

    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("::error::pyproject.toml not found")
        sys.exit(1)

    version = get_pyproject_version(pyproject_path)

    print(f"Tag: {tag}")
    print(f"pyproject.toml version: {version}")

    if tag != version:
        print(f"::error::Tag '{tag}' does not match pyproject.toml version '{version}'")
        sys.exit(1)

    print("Tag matches pyproject.toml version")

    set_output("version", version, dry_run)
    set_output("is_prerelease", str(is_prerelease(version)).lower(), dry_run)


if __name__ == "__main__":
    main()
