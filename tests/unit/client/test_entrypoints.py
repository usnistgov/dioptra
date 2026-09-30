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
from unittest.mock import Mock

import pytest

from dioptra.client.entrypoints import EntrypointsCollectionClient


@pytest.mark.parametrize("validate_only", [False, True])
@pytest.mark.parametrize("snapshot_ids", [[], [17, 29]])
def test_modify_sends_complete_exact_snapshot_selection_in_one_put(
    validate_only, snapshot_ids
):
    session = Mock()
    client = EntrypointsCollectionClient(session)
    response = client.modify_by_id(
        entrypoint_id=10,
        name="entrypoint",
        task_graph="selected: {task: []}",
        artifact_graph=None,
        description=None,
        parameters=None,
        artifact_parameters=None,
        queues=None,
        plugin_snapshot_ids=snapshot_ids,
        artifact_plugin_snapshot_ids=[31],
        validate_only=validate_only,
    )
    assert response is session.put.return_value
    session.put.assert_called_once_with(
        client.url,
        "10",
        params={"validateOnly": validate_only},
        json_={
            "name": "entrypoint",
            "taskGraph": "selected: {task: []}",
            "pluginSnapshotIds": snapshot_ids,
            "artifactPluginSnapshotIds": [31],
        },
    )
    session.get.assert_not_called()
    session.post.assert_not_called()
    session.delete.assert_not_called()


@pytest.mark.parametrize(
    "missing", ["plugin_snapshot_ids", "artifact_plugin_snapshot_ids"]
)
def test_modify_requires_both_snapshot_lists(missing):
    session = Mock()
    client = EntrypointsCollectionClient(session)
    arguments = {
        "entrypoint_id": 10,
        "name": "entrypoint",
        "task_graph": "graph",
        "artifact_graph": None,
        "description": None,
        "parameters": None,
        "artifact_parameters": None,
        "queues": None,
        "plugin_snapshot_ids": [],
        "artifact_plugin_snapshot_ids": [],
    }
    arguments.pop(missing)
    with pytest.raises(TypeError, match=missing):
        client.modify_by_id(**arguments)
    assert session.mock_calls == []
