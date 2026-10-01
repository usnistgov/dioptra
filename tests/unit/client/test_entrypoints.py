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

import pytest

from dioptra.client.entrypoints import EntrypointsCollectionClient
from dioptra.client.sessions import DioptraRequestsSession


@pytest.fixture
def recorded_session(monkeypatch):
    """Use real URL construction while recording every transport request."""
    session = DioptraRequestsSession("https://example.test/api/v1")
    requests = []
    response = object()

    def record_request(method_name, url, **kwargs):
        requests.append((method_name, url, kwargs))
        return response

    monkeypatch.setattr(session, "make_request", record_request)
    return session, requests, response


@pytest.mark.parametrize("validate_only", [False, True])
@pytest.mark.parametrize(
    "task_snapshot_ids, artifact_snapshot_ids",
    [
        pytest.param([], [31], id="empty-task-list"),
        pytest.param([17, 29], [], id="empty-artifact-list"),
        pytest.param([17, 29], [31, 43], id="nonempty-lists"),
    ],
)
def test_modify_sends_complete_exact_snapshot_selection_in_one_put(
    recorded_session, validate_only, task_snapshot_ids, artifact_snapshot_ids
):
    session, requests, expected_response = recorded_session
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
        plugin_snapshot_ids=task_snapshot_ids,
        artifact_plugin_snapshot_ids=artifact_snapshot_ids,
        validate_only=validate_only,
    )
    assert response is expected_response
    assert requests == [
        (
            "put",
            "https://example.test/api/v1/entrypoints/10",
            {
                "params": {"validateOnly": validate_only},
                "json_": {
                    "name": "entrypoint",
                    "taskGraph": "selected: {task: []}",
                    "pluginSnapshotIds": task_snapshot_ids,
                    "artifactPluginSnapshotIds": artifact_snapshot_ids,
                },
            },
        )
    ]
    assert session._session is None


@pytest.mark.parametrize(
    "missing", ["plugin_snapshot_ids", "artifact_plugin_snapshot_ids"]
)
def test_modify_requires_both_snapshot_lists(recorded_session, missing):
    session, requests, _ = recorded_session
    client = EntrypointsCollectionClient(session)
    arguments: dict[str, Any] = {
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
    assert requests == []
    assert session._session is None
