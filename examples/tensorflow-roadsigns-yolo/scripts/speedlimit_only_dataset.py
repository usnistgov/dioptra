import itertools
import os
from contextlib import contextmanager
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

# Source: https://stackoverflow.com/a/42441759
@contextmanager
def working_directory(path: Path):
    """Changes the working directory and returns to the previous one on exit."""
    previous_cwd: Path = Path.cwd()

    try:
        os.chdir(path)

    except FileNotFoundError as err:
        raise FileNotFoundError(
            f"The path '{path}' is not a valid directory."
        ) from err

    try:
        yield

    finally:
        os.chdir(previous_cwd)


def walk_dirs_and_soft_link_images_and_render_xml(
    source_dirs: Iterable[Tuple[Union[str, Path], str]],
    dest_dir: Union[str, Path],
    splits: Dict[str, Dict[str, str]],
    image_suffix_whitelist: Iterable[str],
    annotations_dirname: str = "annotations",
    images_dirname: str = "images",
    overwrite: bool = False,
):

    image_suffix_whitelist = prepare_suffix_whitelist(image_suffix_whitelist)
    source_dest_mappings: List[Iterator[Dict[str, Path]]] = []

    dest_dir = Path(dest_dir)
    dest_training_dir: Path = dest_dir / "training"
    dest_evaluation_dir: Path = dest_dir / "evaluation"
    dest_testing_dir: Path = dest_dir / "testing"

    dest_training_images_dir: Path = dest_training_dir / images_dirname
    dest_training_annotations_dir: Path = dest_training_dir / annotations_dirname
    dest_evaluation_images_dir: Path = dest_evaluation_dir / images_dirname
    dest_evaluation_annotations_dir: Path = dest_evaluation_dir / annotations_dirname
    dest_testing_images_dir: Path = dest_testing_dir / images_dirname
    dest_testing_annotations_dir: Path = dest_testing_dir / annotations_dirname

    dest_training_images_dir.mkdir(parents=True, exist_ok=True)
    dest_training_annotations_dir.mkdir(parents=True, exist_ok=True)
    dest_evaluation_images_dir.mkdir(parents=True, exist_ok=True)
    dest_evaluation_annotations_dir.mkdir(parents=True, exist_ok=True)
    dest_testing_images_dir.mkdir(parents=True, exist_ok=True)
    dest_testing_annotations_dir.mkdir(parents=True, exist_ok=True)

    dest_images_dirs: Dict[str, Path] = dict(
        training=dest_training_images_dir,
        evaluation=dest_evaluation_images_dir,
        testing=dest_testing_images_dir,
    )
    dest_annotations_dirs: Dict[str, Path] = dict(
        training=dest_training_annotations_dir,
        evaluation=dest_evaluation_annotations_dir,
        testing=dest_testing_annotations_dir,
    )

    for source_dir, source_dataset_name in source_dirs:
        source_dir = Path(source_dir)
        source_images_dir: Path = source_dir / images_dirname
        source_annotations_dir: Path = source_dir / annotations_dirname

        source_dest_mappings.append(
            to_source_dest_mappings(
                source_dataset_name=source_dataset_name,
                source_image_filepaths=find_filepaths(source_images_dir, image_suffix_whitelist),
                source_annotations_dir=source_annotations_dir,
                dest_images_dirs=dest_images_dirs,
                dest_annotations_dirs=dest_annotations_dirs,
                splits=splits,
            )
        )

    for source_dest_mapping in itertools.chain.from_iterable(source_dest_mappings):
        render_and_save_xml(
            source_dest_mapping=source_dest_mapping,
            overwrite=overwrite,
        )
        soft_link_image_file(
            source_dest_mapping=source_dest_mapping,
            overwrite=overwrite,
        )


def load_xml(filepath) -> Tuple[Path, Optional[ElementTree]]:
    logger: BoundLogger = LOGGER.new(
        filepath=str(filepath),
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


def extract_roadsigns_annotation_data_from_xml(tree):
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

    # contains_only_speedlimit = [x["name"] == "speedlimit" for x in objects]

    # if contains_only_speedlimit and all(contains_only_speedlimit):
    return dict(
        image_file=image_file,
        image_width=image_width,
        image_height=image_height,
        image_depth=image_depth,
        image_objects=objects,
    )

    # return None


def extract_gtsdb_annotation_data_from_xml(tree):
    def set_object_name(x) -> str:
        object_id: int = int(x.find("./id").text.strip())
        object_name: str = x.find("./name").text.strip()

        if object_id in speedlimit_ids:
            return "speedlimit"

        return object_name

    speedlimit_ids = {0, 1, 2, 3, 4, 5, 7, 8}

    image_file = tree.find(".//filename").text.strip()
    image_width = tree.find(".//size/width").text.strip()
    image_height = tree.find(".//size/height").text.strip()
    image_depth = tree.find(".//size/depth").text.strip()
    objects = [
        dict(
            name=set_object_name(x),
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
    source_dataset_name: str = source_dest_mapping["source_dataset_name"]

    logger: BoundLogger = LOGGER.new(
        filepath=str(filepath),
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

    extract_func = dict(
        roadsigns=extract_roadsigns_annotation_data_from_xml,
        gtsdb=extract_gtsdb_annotation_data_from_xml,
    )[source_dataset_name]

    params: Optional[Dict[str, Any]] = extract_func(tree)

    if params is None:
        logger.debug(
            "Skipping XML export, only including speed limit signs in dataset."
        )
        return filepath, None

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


def soft_link_image_file(
    source_dest_mapping: Dict[str, Path], overwrite: bool = False
) -> Tuple[Path, Optional[Path]]:
    def outfile_exists():
        return outfile.is_file()

    def annotation_outfile_exists():
        return annotation_outfile.is_file()

    filepath: Path = source_dest_mapping["source_image_filepath"]
    outfile: Path = source_dest_mapping["dest_image_filepath"]
    annotation_outfile: Path = source_dest_mapping["dest_annotation_filepath"]
    dest_dir: Path = outfile.parent

    rel_filepath: Path = Path(os.path.relpath(filepath, dest_dir))

    logger: BoundLogger = LOGGER.new(
        filepath=str(filepath),
        rel_filepath=str(rel_filepath),
    )

    if not annotation_outfile_exists():
        logger.debug(
            "Skipping image soft-link, only including speed limit signs in dataset."
        )
        return filepath, None

    if outfile_exists() and not overwrite:
        logger.debug(
            "File already exists at filepath, skipping...",
            outfile=str(outfile),
        )
        return filepath, outfile

    try:
        with working_directory(dest_dir):
            os.symlink(
                src=os.path.relpath(filepath, dest_dir),
                dst=outfile.name,
            )

        logger.info("Image soft-linked", outfile=str(outfile), working_directory=dest_dir)
        return filepath, outfile

    except (IOError, OSError, FileNotFoundError, SameFileError):
        logger.exception("Image soft-linking failed, skipping...", outfile=str(outfile), working_directory=dest_dir)
        return filepath, None


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


def to_source_annotation_filepath(
    source_image_filepath: Path, source_annotations_dir: Path
) -> Path:
    return (
        source_annotations_dir / source_image_filepath.with_suffix(".xml").name
    )


def to_dest_image_filepath(
    source_dataset_name: str, source_image_filepath: Path, dest_images_dir: Path
) -> Path:
    image_filename: str = source_image_filepath.name

    if source_dataset_name == "gtsdb":
        image_filename = f"00000_gtsdb{image_filename}"

    return dest_images_dir / image_filename


def to_dest_annotation_filepath(
    dest_image_filepath: Path, dest_annotations_dir: Path
) -> Path:
    return dest_annotations_dir / dest_image_filepath.with_suffix(".xml").name


def to_source_dest_mappings(
    source_dataset_name: str,
    source_image_filepaths: Iterator[Path],
    source_annotations_dir: Path,
    dest_images_dirs: Dict[str, Path],
    dest_annotations_dirs: Dict[str, Path],
    splits: Dict[str, Dict[str, str]],
) -> Iterator[Dict[str, Path]]:
    for source_image_filepath in source_image_filepaths:
        partition: Optional[str] = splits[source_dataset_name].get(source_image_filepath.name)

        if partition is None:
            continue

        source_annotation_filepath: Path = to_source_annotation_filepath(
            source_image_filepath, source_annotations_dir
        )
        dest_image_filepath: Path = to_dest_image_filepath(
            source_dataset_name, source_image_filepath, dest_images_dirs[partition]
        )
        dest_annotation_filepath: Path = to_dest_annotation_filepath(
            dest_image_filepath, dest_annotations_dirs[partition]
        )

        yield {
            "source_dataset_name": source_dataset_name,
            "source_image_filepath": source_image_filepath,
            "source_annotation_filepath": source_annotation_filepath,
            "dest_image_filepath": dest_image_filepath,
            "dest_annotation_filepath": dest_annotation_filepath,
        }


def make_speedlimit_only_filelist(
    roadsigns_images_dir: Union[str, Path],
    roadsigns_annotations_dir: Union[str, Path],
    gtsdb_images_dir: Union[str, Path],
    gtsdb_annotations_dir: Union[str, Path],
) -> Tuple[Path, Optional[Path]]:
    gtsdb_annotations = []
    roadsigns_annotations = []

    for fp in gtsdb_annotations_dir.glob("*.xml"):
        gtsdb_annotations.append(extract_gtsdb_annotation_data_from_xml(load_xml(fp)[1]))

    for fp in roadsigns_annotations_dir.glob("*.xml"):
        roadsigns_annotations.append(extract_roadsigns_annotation_data_from_xml(load_xml(fp)[1]))

    gtsdb_speedlimit_only_annotations = []
    roadsigns_speedlimit_only_annotations = []

    for annotation in gtsdb_annotations:
        contains_only_speedlimit = [x["name"] == "speedlimit" for x in annotation["image_objects"]]
        if contains_only_speedlimit and all(contains_only_speedlimit):
            gtsdb_speedlimit_only_annotations.append({
                "annotation_file": str((gtsdb_annotations_dir / annotation["image_file"]).with_suffix(".xml")),
                "image_file": str(gtsdb_images_dir / annotation["image_file"]),
                "image_track": "00000",
                "num_image_objects": len(annotation["image_objects"]),
                "source_dataset_name": "gtsdb"
            })

    for annotation in roadsigns_annotations:
        contains_only_speedlimit = [x["name"] == "speedlimit" for x in annotation["image_objects"]]
        if contains_only_speedlimit and all(contains_only_speedlimit):
            roadsigns_speedlimit_only_annotations.append({
                "annotation_file": str((roadsigns_annotations_dir / annotation["image_file"]).with_suffix(".xml")),
                "image_file": str(roadsigns_images_dir / annotation["image_file"]),
                "image_track": annotation["image_file"].rstrip(".png").split("_")[0],
                "num_image_objects": len(annotation["image_objects"]),
                "source_dataset_name": "roadsigns"
            })

    return list(itertools.chain(
        gtsdb_speedlimit_only_annotations,
        roadsigns_speedlimit_only_annotations,
    ))
