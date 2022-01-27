import os
import re
import shutil
from functools import partial
from multiprocessing import Pool, current_process
from pathlib import Path
from shutil import SameFileError
from typing import Any, Dict, Iterable, Iterator, List, Optional, Set, Tuple, Union

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


def walk_dir_and_copy_images_and_render_xml(
    source_dir: Union[str, Path],
    dest_dir: Union[str, Path],
    image_suffix_whitelist: Iterable[str],
    annotations_dirname: str = "annotations",
    images_dirname: str = "images",
    n_workers: Optional[int] = None,
    worker_chunksize: int = 100,
    overwrite: bool = False,
):
    def to_full_filepath(dirpath, filenames) -> List[Path]:
        return [Path(dirpath) / filename for filename in filenames]

    def prepend_missing_dot(x: str) -> str:
        if x.startswith("."):
            return x

        return f".{x}"

    def prepare_suffix_whitelist(suffixes: Iterable[str]) -> Set[str]:
        return {prepend_missing_dot(x.lower()) for x in suffixes}

    def find_filepaths(root_dir: Path, suffix_whitelist: Set[str]) -> Iterator[Path]:
        for dirpath, _, filenames in os.walk(root_dir):
            for fp in to_full_filepath(dirpath, filenames):
                if fp.suffix.lower() in suffix_whitelist:
                    yield fp

    def extract_filestem_components(filestem) -> Dict[str, Any]:
        filestem_components = re.match(
            r"(?P<name_prefix>\w+?)(?P<id>\d+)", filestem
        ).groupdict()

        return {
            "id": int(filestem_components["id"]),
            "name_prefix": filestem_components["name_prefix"],
        }

    def extract_track_id(parent_dir: Path) -> str:
        track_dir_components = re.match(
            r"(?P<name_prefix>\w+?)(?P<id>\d+)", parent_dir
        ).groupdict()

        return track_dir_components["id"]

    def to_source_annotation_filepath(
        source_image_filepath: Path, source_annotations_dir: Path
    ) -> Path:
        filestem_components = extract_filestem_components(source_image_filepath.stem)
        return (
            source_annotations_dir
            / f"{filestem_components['name_prefix']}{filestem_components['id']}.xml"
        )

    def to_dest_image_filepath(
        source_image_filepath: Path, source_images_dir: Path, dest_images_dir: Path
    ) -> Path:
        filestem_components = extract_filestem_components(source_image_filepath.stem)
        file_suffix = source_image_filepath.suffix
        source_image_parent_dir = source_image_filepath.parent
        track_id = "00000"

        if source_image_parent_dir != source_images_dir:
            track_id = extract_track_id(source_image_filepath.parent.name)

        dest_image_filename = f"{track_id}_{filestem_components['name_prefix']}{filestem_components['id']}{file_suffix}"
        return dest_images_dir / dest_image_filename

    def to_dest_annotation_filepath(
        dest_image_filepath: Path, dest_annotations_dir: Path
    ) -> Path:
        return dest_annotations_dir / dest_image_filepath.with_suffix(".xml").name

    def to_source_dest_mappings(
        source_image_filepaths: Iterator[Path],
        source_images_dir: Path,
        source_annotations_dir: Path,
        dest_images_dir: Path,
        dest_annotations_dir: Path,
    ) -> Iterator[Dict[str, Path]]:
        for source_image_filepath in source_image_filepaths:
            source_annotation_filepath: Path = to_source_annotation_filepath(
                source_image_filepath, source_annotations_dir
            )
            dest_image_filepath: Path = to_dest_image_filepath(
                source_image_filepath, source_images_dir, dest_images_dir
            )
            dest_annotation_filepath: Path = to_dest_annotation_filepath(
                dest_image_filepath, dest_annotations_dir
            )

            yield {
                "source_image_filepath": source_image_filepath,
                "source_annotation_filepath": source_annotation_filepath,
                "dest_image_filepath": dest_image_filepath,
                "dest_annotation_filepath": dest_annotation_filepath,
            }

    with Pool(processes=n_workers) as pool:
        source_dir = Path(source_dir)
        dest_dir = Path(dest_dir)
        image_suffix_whitelist = prepare_suffix_whitelist(image_suffix_whitelist)

        source_images_dir: Path = source_dir / images_dirname
        source_annotations_dir: Path = source_dir / annotations_dirname
        dest_images_dir: Path = dest_dir / images_dirname
        dest_annotations_dir: Path = dest_dir / annotations_dirname

        dest_images_dir.mkdir(parents=True, exist_ok=True)
        dest_annotations_dir.mkdir(parents=True, exist_ok=True)

        source_dest_mappings: Iterator[Dict[str, Path]] = to_source_dest_mappings(
            source_image_filepaths=find_filepaths(source_images_dir, image_suffix_whitelist),
            source_images_dir=source_images_dir,
            source_annotations_dir=source_annotations_dir,
            dest_images_dir=dest_images_dir,
            dest_annotations_dir=dest_annotations_dir,
        )

        image_func = partial(
            copy_image_file,
            overwrite=overwrite,
        )

        image_results = pool.imap_unordered(
            image_func, source_dest_mappings, chunksize=worker_chunksize
        )

        for _ in image_results:
            pass

        # Need to reset iterator if used more than once
        source_dest_mappings = to_source_dest_mappings(
            source_image_filepaths=find_filepaths(source_images_dir, image_suffix_whitelist),
            source_images_dir=source_images_dir,
            source_annotations_dir=source_annotations_dir,
            dest_images_dir=dest_images_dir,
            dest_annotations_dir=dest_annotations_dir,
        )

        annotation_func = partial(
            render_and_save_xml,
            overwrite=overwrite,
        )

        annotation_results = pool.imap_unordered(
            annotation_func, source_dest_mappings, chunksize=worker_chunksize
        )

        for _ in annotation_results:
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
    image_file = tree.find(".//filename").text.strip()
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
    source_dest_mapping: Dict[str, Path], overwrite: bool = False
) -> Tuple[Path, Optional[Path]]:
    def outfile_exists():
        return outfile.is_file()

    filepath: Path = source_dest_mapping["source_annotation_filepath"]
    outfile: Path = source_dest_mapping["dest_annotation_filepath"]

    logger: BoundLogger = LOGGER.new(
        filepath=str(filepath),
        process=current_process().name,
    )

    if outfile_exists() and not overwrite:
        logger.debug(
            "File already exists at filepath, skipping...",
            outfile=str(outfile),
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
    params["image_file"] = source_dest_mapping["dest_image_filepath"].name
    xml_string: str = render_xml(template=template, params=params)

    try:
        with outfile.open("wt") as f:
            f.write(xml_string)

        logger.info("XML exported", outfile=str(outfile))
        return filepath, outfile

    except (IOError, OSError, FileNotFoundError):
        logger.exception("XML export failed, skipping...", outfile=str(outfile))
        return filepath, None


def copy_image_file(
    source_dest_mapping: Dict[str, Path], overwrite: bool = False
) -> Tuple[Path, Optional[Path]]:
    def outfile_exists():
        return outfile.is_file()

    filepath: Path = source_dest_mapping["source_image_filepath"]
    outfile: Path = source_dest_mapping["dest_image_filepath"]

    logger: BoundLogger = LOGGER.new(
        filepath=str(filepath),
        process=current_process().name,
    )

    if outfile_exists() and not overwrite:
        logger.debug(
            "File already exists at filepath, skipping...",
            outfile=str(outfile),
        )
        return filepath, outfile

    try:
        shutil.copy(src=filepath, dst=outfile)
        logger.info("Image copied", outfile=str(outfile))
        return filepath, outfile

    except (IOError, OSError, FileNotFoundError, SameFileError):
        logger.exception("Image copy failed, skipping...", outfile=str(outfile))
        return filepath, None
