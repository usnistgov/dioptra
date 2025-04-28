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

from http import HTTPStatus
from typing import Any

from dioptra.client.base import (
    CollectionClient,
    DioptraResponseProtocol,
    JSONDecodeError,
    SubCollectionClient,
)

from dioptra.restapi.utils import find_non_unique
from .lib import helpers

def assert_http_response_matches_expected(
    response: DioptraResponseProtocol,
    expected: list[dict[str, Any]],
    sort_by: str | None,
) -> None:
    """Assert that the provided response and expected response match depending
    on the provided sort_by criteria."""

    if sort_by is None:
        # A sort order was not given in the request, so we must not assume a
        # particular order in the response.
        contents_matches = match_normalized_json(response, expected)
    else:
        contents_matches = helpers.convert_response_to_dict(response)["data"] == expected
    assert response.status_code == HTTPStatus.OK and contents_matches


def assert_retrieving_resource_works(
    dioptra_client: (
        SubCollectionClient[DioptraResponseProtocol, DioptraResponseProtocol]
        | CollectionClient[DioptraResponseProtocol, DioptraResponseProtocol]
    ),
    expected: list[dict[str, Any]],
    group_id: int | None = None,
    sort_by: str | None = None,
    descending: bool | None = None,
    search: str | None = None,
    paging_info: dict[str, Any] | None = None,
) -> None:
    """Build the query string from the provided parameters"""
    query_string: dict[str, Any] = {}

    if sort_by is not None:
        query_string["sort_by"] = sort_by

    if descending is not None:
        query_string["descending"] = descending

    if group_id is not None:
        query_string["group_id"] = group_id

    if search is not None:
        query_string["search"] = search

    if paging_info is not None:
        query_string["index"] = paging_info["index"]
        query_string["page_length"] = paging_info["page_length"]

    response = dioptra_client.get(**query_string)  # type: ignore

    assert_http_response_matches_expected(
        response=response, expected=expected, sort_by=sort_by
    )


def match_normalized_json(
    original_entity: DioptraResponseProtocol | list[dict[str, Any]],
    expected_json_entity: DioptraResponseProtocol | list[dict[str, Any]],
) -> bool:
    """Compares, after it has transformed and normalized the response or json data

    Args:
        original_entity (DioptraResponseProtocol | list[dict[str, Any]]): Either response or Json of the response
        expected_json_entity (DioptraResponseProtocol | list[dict[str, Any]]): Expected or a response-like object of the expected

    Returns:
        bool: True if both object are a match, False - otherwise
    """

    def sort_protocol(pre_json: DioptraResponseProtocol):
        return sorted(helpers.convert_response_to_dict(pre_json)["data"], key=lambda d: d["id"])

    def sort_json(json_entity: list[dict[str, Any]]):
        return sorted(json_entity, key=lambda d: d["id"])

    def sort_object(entity: DioptraResponseProtocol | list[dict[str, Any]]):
        json_like_data = list(dict())
        if isinstance(entity, list):
            json_like_data = sort_json(entity)
        else:
            json_like_data = sort_protocol(entity)
        return json_like_data

    original_data = sort_object(original_entity)
    expected_data = sort_object(expected_json_entity)
    return original_data == expected_data


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


