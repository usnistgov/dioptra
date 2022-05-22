import os
from functools import partial
from multiprocessing import Pool, current_process
from pathlib import Path
from typing import Iterable, Iterator, List, Optional, Set, Tuple, Union

import structlog
from PIL import Image
from structlog.stdlib import BoundLogger

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def walk_dir_and_convert_images(
    root_dir: Union[str, Path],
    suffix_whitelist: Iterable[str],
    validate_matching_suffix: bool = False,
    n_workers: Optional[int] = None,
    worker_chunksize: int = 100,
):
    def to_full_filepath(dirpath, filenames) -> List[Path]:
        return [Path(dirpath) / filename for filename in filenames]

    def prepend_missing_dot(x: str) -> str:
        if x.startswith("."):
            return x

        return f".{x}"

    def prepare_suffix_whitelist(suffixes: Iterable[str]) -> Set[str]:
        return {prepend_missing_dot(x.lower()) for x in suffixes}

    def find_image_filepaths(root_dir: Path, suffix_whitelist) -> Iterator[Path]:
        for dirpath, _, filenames in os.walk(root_dir):
            for fp in to_full_filepath(dirpath, filenames):
                if fp.suffix.lower() in suffix_whitelist:
                    yield fp

    with Pool(processes=n_workers) as pool:
        root_dir = Path(root_dir)
        suffix_whitelist = prepare_suffix_whitelist(suffix_whitelist)
        image_filepaths: Iterator[Path] = find_image_filepaths(
            root_dir, suffix_whitelist
        )
        worker_func = partial(
            convert_image_to_png, validate_matching_suffix=validate_matching_suffix
        )

        results = pool.imap_unordered(worker_func, image_filepaths, chunksize=worker_chunksize)

        for _ in results:
            pass


def convert_image_to_png(
    filepath, validate_matching_suffix: bool = False
) -> Tuple[Path, Optional[Path]]:
    logger: BoundLogger = LOGGER.new(
        filepath=str(filepath),
        validate_matching_suffix=validate_matching_suffix,
        process=current_process().name,
    )

    def outfile_format_matches_infile_format():
        matching_suffix: bool = (
            filepath.with_suffix(filepath.suffix.lower()).name == outfile.name
        )

        if matching_suffix and validate_matching_suffix:
            return validate_image_format(filepath, validation_format="png")

        return matching_suffix

    def outfile_exists():
        return Path(outfile).is_file()

    filepath = Path(filepath)

    if not filepath.is_file():
        logger.warning("File not found, skipping...")
        return filepath, None

    outfile = filepath.with_suffix(".png")

    if outfile_format_matches_infile_format() or outfile_exists():
        logger.info(
            "File is already saved to the PNG format, skipping...",
        )
        return filepath, None

    try:
        with Image.open(str(filepath)) as im:
            im.save(str(outfile))

        logger.info("File converted to PNG", outfile=str(outfile))
        return filepath, outfile

    except OSError:
        logger.warning("PNG conversion failed, skipping...")
        return filepath, None


def validate_image_format(filepath, validation_format: str = "png"):
    try:
        with Image.open(str(filepath)) as im:
            return im.format == validation_format

    except OSError:
        return False
