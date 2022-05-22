import os
from csv import DictReader
from functools import partial
from multiprocessing import Pool, current_process
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import structlog
from PIL import Image
from jinja2 import Environment, Template
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()


ANNOTATION_TEMPLATE = """<annotation>
    <folder>images</folder>
    <filename>{{ image_file }}</filename>
    <size>
        <width>{{ image_width }}</width>
        <height>{{ image_height }}</height>
        <depth>{{ image_depth }}</depth>
    </size>
    <segmented>0</segmented>
    {% for object in image_objects %}
    <object>
        <id>{{ object.object_id }}</id>
        <name>{{ object.name }}</name>
        <supercategory>{{ object.supercategory }}</supercategory>
        <pose>Unspecified</pose>
        <truncated>0</truncated>
        <occluded>0</occluded>
        <difficult>0</difficult>
        <bndbox>
            <xmin>{{ object.bndbox_xmin }}</xmin>
            <ymin>{{ object.bndbox_ymin }}</ymin>
            <xmax>{{ object.bndbox_xmax }}</xmax>
            <ymax>{{ object.bndbox_ymax }}</ymax>
        </bndbox>
    </object>
    {% endfor %}
</annotation>
"""

CLASS_ID_MAPPING = {
    "0": "speed limit 20",
    "1": "speed limit 30",
    "2": "speed limit 50",
    "3": "speed limit 60",
    "4": "speed limit 70",
    "5": "speed limit 80",
    "6": "restriction ends 80",
    "7": "speed limit 100",
    "8": "speed limit 120",
    "9": "no overtaking",
    "10": "no overtaking (trucks)",
    "11": "priority at next intersection",
    "12": "priority road",
    "13": "give way",
    "14": "stop",
    "15": "no traffic both ways",
    "16": "no trucks",
    "17": "no entry",
    "18": "danger",
    "19": "bend left",
    "20": "bend right",
    "21": "bend",
    "22": "uneven road",
    "23": "slippery road",
    "24": "road narrows",
    "25": "construction",
    "26": "traffic signal",
    "27": "pedestrian crossing",
    "28": "school crossing",
    "29": "cycles crossing",
    "30": "snow",
    "31": "animals",
    "32": "restriction ends",
    "33": "go right",
    "34": "go left",
    "35": "go straight",
    "36": "go right or straight",
    "37": "go left or straight",
    "38": "keep right",
    "39": "keep left",
    "40": "roundabout",
    "41": "restriction ends (overtaking)",
    "42": "restriction ends (overtaking (trucks))",
}

# prohibitory: circular, white ground with red border
# mandatory: circular, blue ground
# danger: triangular, white ground with red border
# other: other shapes
CLASS_ID_SUPERCATEGORY_MAPPING = {
    "0": "prohibitory",
    "1": "prohibitory",
    "2": "prohibitory",
    "3": "prohibitory",
    "4": "prohibitory",
    "5": "prohibitory",
    "6": "other",
    "7": "prohibitory",
    "8": "prohibitory",
    "9": "prohibitory",
    "10": "prohibitory",
    "11": "danger",
    "12": "other",
    "13": "other",
    "14": "other",
    "15": "prohibitory",
    "16": "prohibitory",
    "17": "other",
    "18": "danger",
    "19": "danger",
    "20": "danger",
    "21": "danger",
    "22": "danger",
    "23": "danger",
    "24": "danger",
    "25": "danger",
    "26": "danger",
    "27": "danger",
    "28": "danger",
    "29": "danger",
    "30": "danger",
    "31": "danger",
    "32": "other",
    "33": "mandatory",
    "34": "mandatory",
    "35": "mandatory",
    "36": "mandatory",
    "37": "mandatory",
    "38": "mandatory",
    "39": "mandatory",
    "40": "mandatory",
    "41": "other",
    "42": "other",
}


def walk_dir_and_render_xml(
    source_dir: Union[str, Path],
    dest_dir: Union[str, Path],
    ground_truth_filename: str = "gt.txt",
    n_workers: Optional[int] = None,
    worker_chunksize: int = 100,
    overwrite: bool = False,
):
    def find_image_filepaths(source_dir: Path) -> Iterator[Path]:
        for fp in source_dir.glob("*.png"):
            yield fp.resolve()

    with Pool(processes=n_workers) as pool:
        source_dir = Path(source_dir)
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        image_filepaths: Iterator[Path] = find_image_filepaths(source_dir)
        ground_truth: Dict[str, Any] = load_ground_truth_csv(source_dir / ground_truth_filename)
        worker_func = partial(
            render_and_save_xml,
            dest_dir=dest_dir,
            ground_truth=ground_truth,
            overwrite=overwrite,
        )

        results = pool.imap_unordered(
            worker_func, image_filepaths, chunksize=worker_chunksize
        )

        for _ in results:
            pass


def load_ground_truth_csv(filepath) -> Dict[str, Any]:
    logger: BoundLogger = LOGGER.new(
        filepath=str(filepath),
        process=current_process().name,
    )

    filepath = Path(filepath)
    fieldnames = ["filename", "xmin", "ymin", "xmax", "ymax", "class_id"]
    data = {}

    try:
        with filepath.open("r") as f:
            reader = DictReader(f, fieldnames=fieldnames, delimiter=";")
            for row in reader:
                key = str(Path(row["filename"]).with_suffix(".png"))

                if key not in data:
                    data[key] = []

                data[key].append({
                    "name": CLASS_ID_MAPPING[str(row["class_id"]).strip()],
                    "supercategory": CLASS_ID_SUPERCATEGORY_MAPPING[str(row["class_id"]).strip()],
                    "object_id": str(row["class_id"]).strip(),
                    "bndbox_xmin": int(row["xmin"].strip()),
                    "bndbox_ymin": int(row["ymin"].strip()),
                    "bndbox_xmax": int(row["xmax"].strip()),
                    "bndbox_ymax": int(row["ymax"].strip()),
                })

        logger.debug("Ground truth file loaded successfully")
        return data

    except FileNotFoundError as e:
        logger.exception("File not found")
        raise e

    except OSError as e:
        logger.exception("Unable to load ground truth file")
        raise e


def render_xml(template: Template, params: Dict[str, Any]) -> str:
    return template.render(params)


def render_and_save_xml(
    filepath: Path, dest_dir: Path, ground_truth: Dict[str, Any], overwrite: bool = False,
) -> Tuple[Path, Optional[Path]]:
    logger: BoundLogger = LOGGER.new(
        filepath=str(filepath),
        process=current_process().name,
    )

    def outfile_exists():
        return Path(outfile).is_file()

    outfile: Path = dest_dir / filepath.with_suffix(".xml").name

    if outfile_exists() and not overwrite:
        logger.debug(
            "File already exists at filepath, skipping...", outfile=str(outfile)
        )
        return filepath, outfile

    env: Environment = Environment(
        trim_blocks=True, lstrip_blocks=True, autoescape=True
    )
    template = env.from_string(ANNOTATION_TEMPLATE)

    filepath, image_size = extract_image_size(filepath)
    params: Dict[str, Any] = {
        "image_file": filepath.name,
        "image_width": image_size.get("width", "0"),
        "image_height": image_size.get("height", "0"),
        "image_depth": image_size.get("depth", "0"),
        "image_objects": ground_truth.get(filepath.name, []),
    }
    xml_string: str = render_xml(template=template, params=params)

    try:
        with outfile.open("wt") as f:
            f.write(xml_string)

        logger.info("XML exported", outfile=str(outfile))
        return filepath, outfile

    except (IOError, OSError, FileNotFoundError):
        logger.exception("XML export failed, skipping...", outfile=str(outfile))
        return filepath, None


def extract_image_size(
    filepath
) -> Tuple[Path, Optional[Path]]:
    logger: BoundLogger = LOGGER.new(
        filepath=str(filepath),
        process=current_process().name,
    )

    filepath = Path(filepath)

    if not filepath.is_file():
        logger.warning("File not found, skipping...")
        return filepath, None

    try:
        with Image.open(str(filepath)) as im:
            width, height = im.size
            depth = len(im.getbands())

        logger.debug("Extracted image size successfully", width=width, height=height, depth=depth)
        return filepath, {"width": str(width), "height": str(height), "depth": str(depth)}

    except OSError:
        logger.warning("PNG conversion failed, skipping...")
        return filepath, None
