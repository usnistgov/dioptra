import os
import re
from functools import partial
from multiprocessing import Pool, current_process
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import lxml
import structlog
from jinja2 import Environment, Template
from lxml.etree import ElementTree, XMLParser, XMLSyntaxError
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
        <name>{{ object.name }}</name>
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


def walk_dir_and_render_xml(
    source_dir: Union[str, Path],
    dest_dir: Union[str, Path],
    n_workers: Optional[int] = None,
    worker_chunksize: int = 100,
    overwrite: bool = False,
):
    def to_full_filepath(dirpath, filenames) -> List[Path]:
        return [Path(dirpath) / filename for filename in filenames]

    def find_annotation_filepaths(source_dir: Path) -> Iterator[Path]:
        for dirpath, _, filenames in os.walk(source_dir):
            for fp in to_full_filepath(dirpath, filenames):
                if fp.suffix.lower() == ".xml":
                    yield fp

    with Pool(processes=n_workers) as pool:
        source_dir = Path(source_dir)
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        annotation_filepaths: Iterator[Path] = find_annotation_filepaths(source_dir)
        worker_func = partial(
            render_and_save_xml,
            dest_dir=dest_dir,
            overwrite=overwrite,
        )

        results = pool.imap_unordered(
            worker_func, annotation_filepaths, chunksize=worker_chunksize
        )

        for _ in results:
            pass


def load_xml(filepath) -> Tuple[Path, Optional[ElementTree]]:
    logger: BoundLogger = LOGGER.new(
        filepath=str(filepath),
        process=current_process().name,
    )

    filepath = Path(filepath)
    parser = XMLParser(remove_blank_text=True)

    try:
        tree: ElementTree = lxml.etree.parse(str(filepath), parser)
        logger.debug("XML file parsed successfully")
        return filepath, tree

    except XMLSyntaxError:
        logger.warning("File contains malformed XML, skipping...")
        return filepath, None

    except FileNotFoundError:
        logger.warning("File not found, skipping...")
        return filepath, None

    except OSError:
        logger.warning("Unable to read file, skipping...")
        return filepath, None


def extract_annotation_data_from_xml(tree):
    filename = tree.find(".//filename").text.strip()
    image_file = re.findall(r"road[0-9]+$", filename)[0]
    image_file = f"{image_file}.png"
    image_width = tree.find(".//size/width").text.strip()
    image_height = tree.find(".//size/height").text.strip()
    image_depth = tree.find(".//size/depth").text.strip()
    objects = [
        dict(
            name=x.find("./name").text.strip(),
            bndbox_xmin=x.find("./bndbox").find("./xmin").text.strip(),
            bndbox_ymin=x.find("./bndbox").find("./ymin").text.strip(),
            bndbox_xmax=x.find("./bndbox").find("./xmax").text.strip(),
            bndbox_ymax=x.find("./bndbox").find("./ymax").text.strip(),
        )
        for x in tree.findall(".//object")
    ]

    return dict(
        image_file=image_file,
        image_width=image_width,
        image_height=image_height,
        image_depth=image_depth,
        image_objects=objects,
    )


def render_xml(template: Template, params: Dict[str, Any]) -> str:
    return template.render(params)


def render_and_save_xml(
    filepath: Path, dest_dir: Path, overwrite: bool = False
) -> Tuple[Path, Optional[Path]]:
    logger: BoundLogger = LOGGER.new(
        filepath=str(filepath),
        process=current_process().name,
    )

    def outfile_exists():
        return Path(outfile).is_file()

    outfile: Path = dest_dir / filepath.name

    if outfile_exists() and not overwrite:
        logger.debug(
            "File already exists at filepath, skipping...", outfile=str(outfile)
        )
        return filepath, outfile

    filepath, tree = load_xml(filepath)

    if tree is None:
        logger.warning("Failed to load XML file, skipping...")
        return filepath, None

    env: Environment = Environment(
        trim_blocks=True, lstrip_blocks=True, autoescape=True
    )
    template = env.from_string(ANNOTATION_TEMPLATE)

    params: Dict[str, Any] = extract_annotation_data_from_xml(tree)
    xml_string: str = render_xml(template=template, params=params)

    try:
        with outfile.open("wt") as f:
            f.write(xml_string)

        logger.info("XML exported", outfile=str(outfile))
        return filepath, outfile

    except (IOError, OSError, FileNotFoundError):
        logger.exception("XML export failed, skipping...", outfile=str(outfile))
        return filepath, None
