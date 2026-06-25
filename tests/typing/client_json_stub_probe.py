from typing import reveal_type

from dioptra.client import (
    connect_json_dioptra_client,
    connect_response_dioptra_client,
)
from dioptra.client.base import DioptraResponseProtocol, JsonObject, JsonObjectList

json_client = connect_json_dioptra_client("https://example.test")
reveal_type(json_client)

queue_page: JsonObject = json_client.queues.get()
queue_detail: JsonObject = json_client.queues.get_by_id(1)
queue_created: JsonObject = json_client.queues.create(group_id=1, name="queue")
queue_modified: JsonObject = json_client.queues.modify_by_id(
    queue_id=1,
    name="queue",
    description=None,
)
queue_deleted: JsonObject = json_client.queues.delete_by_id(1)

reveal_type(queue_page)
reveal_type(queue_detail)
reveal_type(queue_created)
reveal_type(queue_modified)
reveal_type(queue_deleted)

queue_tags: JsonObjectList = json_client.queues.tags.get(1)
queue_tags_appended: JsonObjectList = json_client.queues.tags.append(1, ids=[1])
queue_tags_modified: JsonObjectList = json_client.queues.tags.modify(1, ids=[1])
queue_tag_removed: JsonObject = json_client.queues.tags.remove(1, tag_id=1)
queue_tags_removed: JsonObject = json_client.queues.tags.remove_all(1)

reveal_type(queue_tags)
reveal_type(queue_tags_appended)
reveal_type(queue_tags_modified)
reveal_type(queue_tag_removed)
reveal_type(queue_tags_removed)

response_client = connect_response_dioptra_client("https://example.test")
reveal_type(response_client)

response: DioptraResponseProtocol = response_client.queues.get_by_id(1)
reveal_type(response)

invalid_queue_object: JsonObject = json_client.queues.tags.get(1)  # type: ignore[assignment]
