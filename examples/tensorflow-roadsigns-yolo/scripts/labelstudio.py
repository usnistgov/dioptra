import re
from dataclasses import asdict, dataclass
from pathlib import Path
from posixpath import join as urljoin
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from xml.etree import ElementTree

import requests


@dataclass
class CreatePrediction:
    task: int
    result: List[Dict[str, Any]]
    score: Optional[float]
    cluster: Optional[int]
    neighbors: Optional[Dict[str, Any]]
    mislabeling: float


def to_xywh_coordinates(bboxes, img_shape):
    bboxes_xywh = []
    for bbox in bboxes:
        width = bbox["xmax"] - bbox["xmin"]
        height = bbox["ymax"] - bbox["ymin"]
        x = bbox["xmin"]
        y = bbox["ymin"]
        bboxes_xywh.append(
            {
                "rectanglelabels": bbox["rectanglelabels"],
                "x": x / img_shape["original_width"] * 100.0,
                "y": y / img_shape["original_height"] * 100.0,
                "width": width / img_shape["original_width"] * 100.0,
                "height": height / img_shape["original_height"] * 100.0,
                "rotation": 0,
            }
        )
    return bboxes_xywh


def create_prediction(endpoint_url, prediction, headers):
    payload = prediction.copy()
    payload["result"] = [
        {**x, **{"to_name": "image", "from_name": "label", "type": "rectanglelabels"}}
        for x in payload["result"]
    ]
    response = requests.post(endpoint_url, json=payload, headers=headers)
    return response


def convert_pascal_xml_file_to_labelstudio_json(filepath, annotations):
    filepath = Path(filepath)
    with filepath.open("rt") as f:
        annotations[filepath.with_suffix(".png").name] = {
            "result": from_pascal_to_labelstudio(ElementTree.fromstring(f.read()))
        }


def make_prediction_obj(project_task, annotations):
    return CreatePrediction(
        task=project_task["id"],
        result=annotations[extract_image_name(project_task)]["result"],
        score=None,
        cluster=None,
        neighbors=None,
        mislabeling=0,
    )


def get_paginated_tasks(
    base_uri,
    project_id,
    headers,
    filters=None,
    ordering=None,
    view_id=None,
    selected_ids=None,
    page: int = 1,
    page_size: int = -1,
    only_ids: bool = False,
):
    query = {
        "filters": filters,
        "ordering": ordering or [],
        "selectedItems": {"all": False, "included": selected_ids}
        if selected_ids
        else {"all": True, "excluded": []},
    }
    params = {
        "project": project_id,
        "page": page,
        "page_size": page_size,
        "view": view_id,
        "query": json.dumps(query),
        "fields": "all",
    }
    if only_ids:
        params["include"] = "id"

    response = requests.get(
        urljoin(base_uri, "api", "dm", "tasks/"), params, headers=headers
    )

    data = response.json()
    tasks = data["tasks"]
    if only_ids:
        data["tasks"] = [task["id"] for task in tasks]

    return data


def extract_image_name(project_task):
    image_name = Path(urlparse(project_task["data"]["image"])[2]).name
    return re.findall(r"road[0-9]+\.png$", image_name)[0]


def from_pascal_to_labelstudio(tree):
    img_shape = extract_image_shape(tree)
    bboxes = to_xywh_coordinates(extract_bboxes(tree), img_shape)
    result = []
    for value in bboxes:
        result.append(
            {
                "original_width": img_shape["original_width"],
                "original_height": img_shape["original_height"],
                "image_rotation": 0,
                "value": value,
            }
        )
    return result


def extract_bboxes(tree):
    objects = tree.findall(".//object")
    bboxes = []
    for obj in objects:
        bboxes.append(
            {
                "rectanglelabels": [obj.find("./name").text],
                "xmin": int(obj.find("./bndbox/xmin").text),
                "ymin": int(obj.find("./bndbox/ymin").text),
                "xmax": int(obj.find("./bndbox/xmax").text),
                "ymax": int(obj.find("./bndbox/ymax").text),
            }
        )

    return bboxes


def extract_image_shape(tree):
    width = int(tree.find(".//size/width").text)
    height = int(tree.find(".//size/height").text)
    depth = int(tree.find(".//size/depth").text)
    return {"original_width": width, "original_height": height, "original_depth": depth}


def main(annotations_dir, auth_token, base_url):
    annotations_dir = Path(annotations_dir)
    xml_files = sorted(list(annotations_dir.glob("*.xml")))
    ls_predictions = urljoin(base_url, "api", "predictions/")
    headers = {"Authorization": f"Token {auth_token}"}

    annotations = {}
    for filepath in xml_files:
        convert_pascal_xml_file_to_labelstudio_json(filepath, annotations)

    project_tasks = get_paginated_tasks(
        base_url, 2, headers=headers, page_size=1000, page=1
    )

    predictions_payload = [
        asdict(make_prediction_obj(x, annotations)) for x in project_tasks["tasks"]
    ]

    for payload in predictions_payload:
        create_prediction(ls_predictions, payload, headers)
