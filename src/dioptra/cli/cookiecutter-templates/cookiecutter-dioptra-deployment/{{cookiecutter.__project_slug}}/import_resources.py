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

"""
This script allows the user to import resources from a git repository into a deployment.
"""

import argparse
import getpass
import os
from http import HTTPStatus

import requests


def main():
    parser = argparse.ArgumentParser(
        "Import Resources",
        description="Import resources from a git repository into a Dioptra deployment.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        type=str,
        default=os.environ.get("DIOPTRA_HOST", "http://localhost:5000"),
        help="The url of the Dioptra deployment.",
    )
    parser.add_argument(
        "--username",
        "-u",
        type=str,
        default=os.environ.get("DIOPTRA_USERNAME"),
        help="The user to authenticate as.",
    )
    parser.add_argument(
        "--password",
        "-p",
        type=str,
        default=os.environ.get("DIOPTRA_PASSWORD"),
        help="The user's password. Leave empty to be prompted.",
    )
    parser.add_argument(
        "--git-url",
        type=str,
        default="https://github.com/usnistgov/dioptra",
        help="The git repository to import resources from.",
    )
    parser.add_argument(
        "--git-branch",
        type=str,
        default=os.environ.get("DIOPTRA_BRANCH", "main"),
        help="The git branch to import resources from.",
    )
    parser.add_argument(
        "--group",
        "-g",
        type=int,
        default=1,
        help="The group into which resouces will be imported.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite any resources with a conflicting name.",
    )
    args = parser.parse_args()

    if not args.username:
        args.username = input("Username: ")

    if not args.password:
        args.password = getpass.getpass("Password: ")

    sess = requests.Session()

    print(f"logging in to dioptra deployment {args.host} with user '{args.username}'")
    response = sess.post(
        f"{args.host}/api/v1/auth/login",
        json={"username": args.username, "password": args.password},
    )
    print(response.json())
    if response.status_code != HTTPStatus.OK:
        return

    print(f"importing resources from {args.git_url}#{args.git_branch}")
    response = sess.post(
        f"{args.host}/api/v1/workflows/resourceImport",
        data={
            "group": args.group,
            "sourceType": "git",
            "gitUrl": f"{args.git_url}#{args.git_branch}",
            "configPath": "extra/dioptra.toml",
            "resolveNameConflictsStrategy": "overwrite" if args.overwrite else "fail",
        },
    )
    print(response.json())


if __name__ == "__main__":
    main()
