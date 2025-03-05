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

from dioptra.client.base import CollectionClient, DioptraResponseProtocol
from dioptra.client.drafts import (
    ModifyResourceDraftsSubCollectionClient,
    NewResourceDraftsSubCollectionClient,
)
from dioptra.client.snapshots import SnapshotsSubCollectionClient
from dioptra.client.tags import TagsSubCollectionClient
from dioptra.client.workflows import WorkflowsCollectionClient

from . import asserts


def run_new_resource_drafts_tests(
    resource_client: CollectionClient[DioptraResponseProtocol],
    draft_client: NewResourceDraftsSubCollectionClient[DioptraResponseProtocol],
    workflow_client: WorkflowsCollectionClient[DioptraResponseProtocol],
    *resource_ids: str | int,
    drafts: dict[str, Any],
    draft1_mod: dict[str, Any],
    draft1_expected: dict[str, Any],
    draft2_expected: dict[str, Any],
    draft1_mod_expected: dict[str, Any],
    group_id: int | None = None,
) -> None:
    # Creation operation tests
    draft1_response = draft_client.create(
        *resource_ids, group_id=group_id, **drafts["draft1"]
    ).json()
    asserts.assert_draft_response_contents_matches_expectations(
        draft1_response, draft1_expected
    )
    asserts.assert_retrieving_draft_by_id_works(
        draft_client,
        *resource_ids,
        draft_id=draft1_response["id"],
        expected=draft1_response,
    )

    draft2_response = draft_client.create(
        *resource_ids, group_id=group_id, **drafts["draft2"]
    ).json()
    asserts.assert_draft_response_contents_matches_expectations(
        draft2_response, draft2_expected
    )
    asserts.assert_retrieving_draft_by_id_works(
        draft_client,
        *resource_ids,
        draft_id=draft2_response["id"],
        expected=draft2_response,
    )
    asserts.assert_retrieving_drafts_works(
        draft_client,
        *resource_ids,
        expected=[draft1_response, draft2_response],
    )

    # Modify operation tests
    response = draft_client.modify(
        *resource_ids, draft_id=draft1_response["id"], **draft1_mod
    ).json()
    asserts.assert_draft_response_contents_matches_expectations(
        response, draft1_mod_expected
    )

    # Delete operation tests
    draft_client.delete(*resource_ids, draft_id=draft1_response["id"])
    asserts.assert_new_draft_is_not_found(
        draft_client, *resource_ids, draft_id=draft1_response["id"]
    )

    # Commit operation tests
    commit_response = workflow_client.commit_draft(draft2_response["id"]).json()
    asserts.assert_new_draft_is_not_found(
        draft_client, *resource_ids, draft_id=draft2_response["id"]
    )
    resource_response = resource_client.get_by_id(*commit_response["id"]).json()
    asserts.assert_resource_contents_match_expectations(
        resource_response, draft2_expected["payload"]
    )


def run_existing_resource_drafts_tests(
    resource_client: CollectionClient[DioptraResponseProtocol],
    draft_client: ModifyResourceDraftsSubCollectionClient[DioptraResponseProtocol],
    workflow_client: WorkflowsCollectionClient[DioptraResponseProtocol],
    *resource_ids: str | int,
    draft: dict[str, Any],
    draft_mod: dict[str, Any],
    draft_expected: dict[str, Any],
    draft_mod_expected: dict[str, Any],
) -> None:
    # Creation operation tests
    response = draft_client.create(*resource_ids, **draft).json()
    asserts.assert_draft_response_contents_matches_expectations(
        response, draft_expected
    )
    asserts.assert_retrieving_draft_by_resource_id_works(
        draft_client, *resource_ids, expected=response
    )
    asserts.assert_creating_another_existing_draft_fails(
        draft_client, *resource_ids, payload=draft
    )

    # Modify operation tests
    response = draft_client.modify(
        *resource_ids, resource_snapshot_id=response["resourceSnapshot"], **draft_mod
    ).json()
    asserts.assert_draft_response_contents_matches_expectations(
        response, draft_mod_expected
    )

    # Delete operation tests
    draft_client.delete(*resource_ids)
    asserts.assert_existing_draft_is_not_found(draft_client, *resource_ids)

    # Commit operation tests
    # This sequence tests the case where a resource that has draft modifications is
    # modified (i.e. a new snapshot is created) before the draft is committed. In this
    # case, the commit should fail until the snapshot ID of the draft is updated to
    # indicate that the user is aware of the changes.
    draft_response = draft_client.create(*resource_ids, **draft).json()
    resource_response = resource_client.modify_by_id(*resource_ids, **draft_mod).json()
    commit_response = workflow_client.commit_draft(draft_response["id"]).json()
    draft_response = draft_client.modify(
        *resource_ids,
        resource_snapshot_id=commit_response["detail"]["curr_snapshot_id"],
        **draft,
    ).json()
    commit_response = workflow_client.commit_draft(draft_response["id"]).json()
    asserts.assert_existing_draft_is_not_found(draft_client, *resource_ids)
    resource_response = resource_client.get_by_id(*commit_response["id"]).json()
    asserts.assert_resource_contents_match_expectations(
        resource_response, draft_expected["payload"]
    )


def run_resource_snapshots_tests(
    client: SnapshotsSubCollectionClient[DioptraResponseProtocol],
    *resource_ids: str | int,
    resource_to_rename: dict[str, Any],
    modified_resource: dict[str, Any],
    drop_additional_fields: list[str] | None = None,
):
    # Remove hasDraft field that isn't present on the snapshot responses
    modified_resource.pop("hasDraft")
    resource_to_rename.pop("hasDraft")

    # If exclude_additional_fields is provided, remove those fields from the expected
    # responses
    if drop_additional_fields:
        for field in drop_additional_fields:
            modified_resource.pop(field)
            resource_to_rename.pop(field)

    # Modify the first resource snapshot fields since a second snapshot was created
    resource_to_rename["latestSnapshot"] = False
    resource_to_rename["lastModifiedOn"] = modified_resource["lastModifiedOn"]

    # Validate retrieval of first snapshot
    asserts.assert_retrieving_snapshot_by_id_works(
        client,
        *resource_ids,
        resource_to_rename["id"],
        snapshot_id=resource_to_rename["snapshot"],
        expected=resource_to_rename,
    )

    # Validate retrieval of second snapshot
    asserts.assert_retrieving_snapshot_by_id_works(
        client,
        *resource_ids,
        modified_resource["id"],
        snapshot_id=modified_resource["snapshot"],
        expected=modified_resource,
    )

    # Validate retrieval of all snapshots
    asserts.assert_retrieving_snapshots_works(
        client,
        *resource_ids,
        resource_to_rename["id"],
        expected=[resource_to_rename, modified_resource],
    )


def run_resource_tag_tests(
    client: TagsSubCollectionClient[DioptraResponseProtocol],
    *resource_ids: str | int,
    tag_ids: list[int],
) -> None:
    # Append operation tests
    response = client.append(*resource_ids, ids=[tag_ids[0], tag_ids[1]])
    asserts.assert_tags_response_contents_matches_expectations(
        response.json(), [tag_ids[0], tag_ids[1]]
    )
    response = client.append(*resource_ids, ids=[tag_ids[1], tag_ids[2]])
    asserts.assert_tags_response_contents_matches_expectations(
        response.json(), [tag_ids[0], tag_ids[1], tag_ids[2]]
    )

    # Remove operation tests
    client.remove(*resource_ids, tag_id=tag_ids[1])
    response = client.get(*resource_ids)
    asserts.assert_tags_response_contents_matches_expectations(
        response.json(), [tag_ids[0], tag_ids[2]]
    )

    # Modify operation tests
    response = client.modify(*resource_ids, ids=[tag_ids[1], tag_ids[2]])
    asserts.assert_tags_response_contents_matches_expectations(
        response.json(), [tag_ids[1], tag_ids[2]]
    )

    # Delete operation tests
    client.remove_all(*resource_ids)
    response = client.get(*resource_ids)
    asserts.assert_tags_response_contents_matches_expectations(response.json(), [])
