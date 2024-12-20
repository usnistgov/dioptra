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
from __future__ import annotations

from dioptra.restapi.utils import find_non_unique


def test_find_non_unique():
    assert (
        len(
            find_non_unique(
                "name",
                [
                    {"name": "hello", "foo": "bar"},
                    {"name": "goodbye", "bar": "foo"},
                    {"name": "hello", "lo": "behold"},
                ],
            )
        )
        == 1
    )

    assert (
        len(
            find_non_unique(
                "name",
                [
                    {"name": "hello", "foo": "bar"},
                    {"name": "goodbye", "bar": "none"},
                    {"name": "today", "lo": "hi"},
                ],
            )
        )
        == 0
    )

    assert (
        len(
            find_non_unique(
                "name",
                [
                    {"name": "hello", "foo": "bar"},
                    {"name": "goodbye", "bar": "none"},
                    {"name": "hello", "lo": "behold"},
                    {"name": "goodbye", "lo": "behold"},
                ],
            )
        )
        == 2
    )
