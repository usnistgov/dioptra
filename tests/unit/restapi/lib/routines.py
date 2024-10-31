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
from typing import Any

from dioptra.client.base import DioptraResponseProtocol
from dioptra.client.drafts import (
    ExistingResourceDraftsSubCollectionClient,
    NewResourceDraftsSubCollectionClient,
)

from . import asserts, asserts_client


def run_new_resource_drafts_tests(
    client: NewResourceDraftsSubCollectionClient[DioptraResponseProtocol],
    *resource_ids: str | int,
    drafts: dict[str, Any],
    draft1_mod: dict[str, Any],
    draft1_expected: dict[str, Any],
    draft2_expected: dict[str, Any],
    draft1_mod_expected: dict[str, Any],
    group_id: int | None = None,
) -> None:
    # Creation operation tests
    draft1_response = client.create(
        *resource_ids, group_id=group_id, **drafts["draft1"]
    ).json()
    asserts.assert_draft_response_contents_matches_expectations(
        draft1_response, draft1_expected
    )
    asserts_client.assert_retrieving_draft_by_id_works(
        client,
        *resource_ids,
        draft_id=draft1_response["id"],
        expected=draft1_response,
    )

    draft2_response = client.create(
        *resource_ids, group_id=group_id, **drafts["draft2"]
    ).json()
    asserts.assert_draft_response_contents_matches_expectations(
        draft2_response, draft2_expected
    )
    asserts_client.assert_retrieving_draft_by_id_works(
        client,
        *resource_ids,
        draft_id=draft2_response["id"],
        expected=draft2_response,
    )
    asserts_client.assert_retrieving_drafts_works(
        client,
        *resource_ids,
        expected=[draft1_response, draft2_response],
    )

    # Modify operation tests
    response = client.modify(
        *resource_ids, draft_id=draft1_response["id"], **draft1_mod
    ).json()
    asserts.assert_draft_response_contents_matches_expectations(
        response, draft1_mod_expected
    )

    # Delete operation tests
    client.delete(*resource_ids, draft_id=draft1_response["id"])
    asserts_client.assert_new_draft_is_not_found(
        client, *resource_ids, draft_id=draft1_response["id"]
    )


def run_existing_resource_drafts_tests(
    client: ExistingResourceDraftsSubCollectionClient[DioptraResponseProtocol],
    *resource_ids: str | int,
    draft: dict[str, Any],
    draft_mod: dict[str, Any],
    draft_expected: dict[str, Any],
    draft_mod_expected: dict[str, Any],
) -> None:
    # Creation operation tests
    response = client.create(*resource_ids, **draft).json()
    asserts.assert_draft_response_contents_matches_expectations(
        response, draft_expected
    )
    asserts_client.assert_retrieving_draft_by_resource_id_works(
        client, *resource_ids, expected=response
    )
    asserts_client.assert_creating_another_existing_draft_fails(
        client, *resource_ids, payload=draft
    )

    # Modify operation tests
    response = client.modify(*resource_ids, **draft_mod).json()
    asserts.assert_draft_response_contents_matches_expectations(
        response, draft_mod_expected
    )

    # Delete operation tests
    client.delete(*resource_ids)
    asserts_client.assert_existing_draft_is_not_found(client, *resource_ids)
