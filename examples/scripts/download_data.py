#!/usr/bin/env python
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
"""Fetch and organize the datasets used in Dioptra's examples and demos.

The Dioptra examples assume that the worker containers have access to datasets nested
under the path /dioptra/data. This path is a host directory or named volume that is
mounted into the worker containers. This script is used to fetch the datasets and store
them in the aforementioned host directory or named volume.

In addition to fetching the datasets, this script automatically organizes the files and
directories so that each dataset follows a consistent and predictable structure. At a
minimum, all of the example datasets are split into a training and testing subset, which
forms the first level of the directory structure. Schematically, this looks like the
following:

    Dataset-Name/
    ├── testing/
    └── training/

If a dataset also has a predefined validation subset, then the directory structure will
be modified as follows:

    Dataset-Name/
    ├── testing/
    ├── training/
    └── validation/

The subsequent levels of the directory structure depend on the machine learning tasks
(modalities) that the dataset supports. At present, this script fetches datasets that
support the following modalities:

- Multi-class image classification (one label per image)
- Object detection

Multi-class image classification datasets sort the images into subdirectories according
to their class label, with the number of subdirectories being equal to the number of
classes in the dataset. Schematically, this looks like the following:

    Dataset-Name/
    ├── testing/
    │   ├── label-1/
    │   │   ├── 00001.png
    │   │   ├── 00002.png
    │   │   ...
    │   ├── label-2/
    │   │   ├── 00011.png
    │   │   ├── 00012.png
    │   │   ...
    └── training/
        ├── label-1/
        │   ├── 00001.png
        │   ├── 00002.png
        │   ...
        ├── label-2/
        │   ├── 00101.png
        │   ├── 00102.png
        │   ...

Object detection datasets follow the PascalVOC format, which separates the images and
annotations (object bounding boxes) into the following folders:

    annotations/   (xml files)
    images/        (png, jpg, etc. files)

The PascalVOC format uses filenames to associate images with their corresponding
annotation. For example, the image file images/00001.png has an associated annotation
file annotations/00001.xml. Schematically, this looks like the following:

    Dataset-Name/
    ├── testing
    │   ├── annotations
    │   │   ├── 00001.xml
    │   │   ├── 00002.xml
    │   │   ...
    │   └── images
    │       ├── 00001.png
    │       ├── 00002.png
    │       ...
    └── training
        ├── annotations
        │   ├── 00001.xml
        │   ├── 00002.xml
        │   ...
        └── images
            ├── 00001.png
            ├── 00002.png
            ...

Classes:
    LabeledImage: A NamedTuple containing the data and metadata for a single labeled
        image.
    ExampleDataset: Defines the interface for the classes that fetch a dataset used in
        one or more of the examples.
    MnistDataset: Fetches the MNIST handwritten digits dataset.
    RoadSignsDataset: Fetches the Road Signs Detection dataset hosted on Kaggle.
    Fruits360Dataset: Fetches the Fruits 360 dataset hosted on Kaggle.
    ImageNetDataset: Fetches the ImageNet Object Localization Challenge dataset hosted
        on Kaggle.
    KaggleApi: A wrapper for the Kaggle API command line tool.

Functions:
    download_kaggle_competition: Download the dataset for a Kaggle competition.
    download_kaggle_dataset: Download a Kaggle dataset.
    unzip_kaggle_dataset: Unzip a Kaggle dataset.
    save_image: Save a numpy array as an image.
    download_dataset: The entrypoint for the Click-based CLI.
    mnist: The Click command for fetching the MNIST dataset.
    roadsigns: The Click command for fetching the Road Signs Detection dataset.
    fruits360: The Click command for fetching the Fruits 360 dataset.
    imagenet: The Click command for fetching the ImageNet dataset.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, Iterable, NamedTuple, cast

import click
import numpy as np
import numpy.typing as npt
from click import Context
from PIL import Image
from rich.console import Console
from upath import UPath

# The try/except ImportError block allows this script to be invoked using:
#     python ./scripts/download_data.py  # OR
#     python -m scripts.download_data
try:
    from .utils import RichConsole

except ImportError:
    from utils import RichConsole

_CURRENT_DIR = Path(__file__).parent
_PATCHES_DIR = _CURRENT_DIR / "patches"
_ROAD_SIGNS_V2_DIR = _PATCHES_DIR / "Road-Sign-Detection-v2"

_CONTEXT_SETTINGS = dict(
    help_option_names=["-h", "--help"],
    show_default=True,
)


class LabeledImage(NamedTuple):
    """The data and metadata for a single labeled image.

    Attributes:
        filename: The name of the image file.
        data: An 8-bit unsigned integer numpy array containing the image data.
        label: The classification label for the image.
    """

    filename: str
    data: npt.NDArray[np.uint8]
    label: str


class ExampleDataset(ABC):
    """A dataset used in one or more of the examples."""

    @abstractmethod
    def fetch(self, output_path: str | Path, overwrite: bool = False) -> str:
        """Fetch the dataset.

        Args:
            output_path: The path to the folder where the example datasets are stored.
            overwrite: If True, fetch the data even if the target folder already exists
                and overwrite any existing data files.

        Returns:
            The path to the folder containing the fetched data source.
        """
        raise NotImplementedError


class MnistDataset(ExampleDataset):
    """The MNIST handwritten digits dataset.

    Each image is stored as a 28x28 grayscale PNG file and sorted into subdirectories
    according to their class label:

        Mnist/
        ├── testing/
        │   ├── 0/
        │   ├── 1/
        │   ├── 2/
        │   ├── 3/
        │   ├── 4/
        │   ├── 5/
        │   ├── 6/
        │   ├── 7/
        │   ├── 8/
        │   └── 9/
        └── training/
            ├── 0/
            ├── 1/
            ├── 2/
            ├── 3/
            ├── 4/
            ├── 5/
            ├── 6/
            ├── 7/
            ├── 8/
            └── 9/

    Attributes:
        data_url: A UPath pointing to a downloadable copy the MNIST dataset.

    License:
        Yann LeCun and Corinna Cortes hold the copyright of MNIST dataset, which is a
        derivative work from original NIST datasets. MNIST dataset is made available
        under the terms of the CC BY-SA 3.0 license
        (https://creativecommons.org/licenses/by-sa/3.0/).
    """

    data_path = UPath(
        "https://storage.googleapis.com/tensorflow/tf-keras-datasets/mnist.npz"
    )

    def fetch(self, output_dir: str | Path, overwrite: bool = False) -> str:
        """Fetch the MNIST dataset.

        Args:
            output_path: The path to the folder where the example datasets are stored.
            overwrite: If True, fetch the MNIST data even if the target folder already
                exists and overwrite any existing data files.

        Returns:
            The path to the folder containing the MNIST dataset.
        """
        dataset_dir = Path(output_dir) / "Mnist"

        if dataset_dir.exists() and not overwrite:
            return str(dataset_dir)

        self._download_images(output_dir=dataset_dir)
        return str(dataset_dir)

    def _download_images(self, output_dir: Path) -> None:
        training_dir: Path = output_dir / "training"
        testing_dir: Path = output_dir / "testing"
        training_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
        testing_dir.mkdir(mode=0o755, parents=True, exist_ok=True)

        with self.data_path.open("rb") as f, np.load(f, allow_pickle=True) as data:  # type: ignore[no-untyped-call] # noqa: B950
            training = self._iter_data(data=data, subset="train")
            testing = self._iter_data(data=data, subset="test")
            self._save_array_as_image_files(images=training, output_dir=training_dir)
            self._save_array_as_image_files(images=testing, output_dir=testing_dir)

    @staticmethod
    def _iter_data(data: Any, subset: str) -> Iterable[LabeledImage]:
        data_x_y = zip(data[f"x_{subset}"], data[f"y_{subset}"])
        for idx, (array, label) in enumerate(data_x_y):
            yield LabeledImage(
                filename=f"{str(idx).zfill(5)}.png",
                data=cast(npt.NDArray[np.uint8], array),
                label=str(label),
            )

    @staticmethod
    def _save_array_as_image_files(
        images: Iterable[LabeledImage], output_dir: Path
    ) -> None:
        for image in images:
            image_filepath = output_dir / image.label / image.filename
            image_filepath.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
            save_image(image_array=image.data, output_filepath=image_filepath)


class RoadSignsDataset(ExampleDataset):
    """The Road Signs Detection dataset hosted on Kaggle.

    This object detection dataset is "patched" after it is downloaded. The dataset patch
    does the following:

    - Splits the data into predefined training and testing sets.
    - Prepends each filename with a 5-digit prefix (00001 through 00136) that
      groups the images into "tracks". The 00000 prefix is reserved for images that do
      not belong to a track.
    - Replaces the original annotations with the updated versions in the
      examples/scripts/patches/Road-Sign-Detection-v2 directory. The updated annotations
      fix mistakes in the classification labels and bounding boxes identified by the
      Dioptra development team.

    Note:
        A track is a sequence of correlated images sampled from a video clip of the same
        physical, real-world object. Because the images within each track are highly
        correlated, each track should either be placed in the training set or the
        testing set as a group. Splitting the images from a single track across the
        training and testing set will result in data leakage.

    The directory structure after patching is as follows:

        Road-Sign-Detection-v2/
        ├── testing/
        │   ├── annotations/
        │   └── images/
        └── training/
            ├── annotations/
            └── images/

    Attributes:
        kaggle_dataset: The name of the Kaggle dataset.
        v2_training_annotations_dir: The path to the directory containing the updated
            training annotations.
        v2_testing_annotations_dir: The path to the directory containing the updated
            testing annotations.
        v2_patch_file: The path to the patch file that is used to split the data into
            predefined training and testing sets and to add a 5-digit prefix to the
            filenames that groups the images into tracks.

    Notes:
        You will need to register for a Kaggle account and obtain an API token in order
        to fetch the dataset using the Kaggle API. For instructions on how to obtain and
        use a Kaggle API token, see
        https://github.com/Kaggle/kaggle-api#api-credentials.

        Dataset URL: https://www.kaggle.com/datasets/andrewmvd/road-sign-detection

    License:
        CC0: Public Domain (https://creativecommons.org/publicdomain/zero/1.0/).
    """

    kaggle_dataset = "andrewmvd/road-sign-detection"
    v2_training_annotations_dir = _ROAD_SIGNS_V2_DIR / "training" / "annotations"
    v2_testing_annotations_dir = _ROAD_SIGNS_V2_DIR / "testing" / "annotations"
    v2_patch_file = _PATCHES_DIR / "road_signs_v2_patch.jsonl"

    def fetch(self, output_dir: str | Path, overwrite: bool = False) -> str:
        """Fetch and patch the Road Signs Detection dataset.

        Args:
            output_path: The path to the folder where the example datasets are stored.
            overwrite: If True, fetch the Road Signs Detection data even if the target
                folder already exists and overwrite any existing data files.

        Returns:
            The path to the folder containing the patched Road Signs Detection dataset.

        Notes:
            Fetching the dataset using the Kaggle API requires the use of an API token.
            For instructions on how to obtain and use a Kaggle API token, see
            https://github.com/Kaggle/kaggle-api#api-credentials.
        """
        v1_dataset_dir = Path(output_dir) / "RoadSignsPascalVOC"
        v2_dataset_dir = Path(output_dir) / _ROAD_SIGNS_V2_DIR.name

        if v2_dataset_dir.exists() and not overwrite:
            return str(v2_dataset_dir)

        download_kaggle_dataset(
            dataset=self.kaggle_dataset,
            output_dir=v1_dataset_dir,
            overwrite=overwrite,
            unzip=True,
        )
        self._apply_v2_patch(output_dir=v2_dataset_dir, overwrite=overwrite)
        shutil.rmtree(path=str(v1_dataset_dir))
        return str(v2_dataset_dir)

    def _apply_v2_patch(self, output_dir: Path, overwrite: bool) -> None:
        for v2_patch_mapping in self._load_v2_patch_file(output_dir.parent):
            destination_dir = Path(v2_patch_mapping["destination"]).parent

            if not destination_dir.exists():
                destination_dir.mkdir(mode=0o755, parents=True)

            shutil.copy(
                src=v2_patch_mapping["source"],
                dst=v2_patch_mapping["destination"],
            )

        shutil.copytree(
            src=str(self.v2_training_annotations_dir),
            dst=str(output_dir / "training" / "annotations"),
            dirs_exist_ok=overwrite,
        )
        shutil.copytree(
            src=str(self.v2_testing_annotations_dir),
            dst=str(output_dir / "testing" / "annotations"),
            dirs_exist_ok=overwrite,
        )
        shutil.copy(
            src=str(self.v2_training_annotations_dir.parent / "coco.json"),
            dst=str(output_dir / "training" / "coco.json"),
        )
        shutil.copy(
            src=str(self.v2_testing_annotations_dir.parent / "coco.json"),
            dst=str(output_dir / "testing" / "coco.json"),
        )

    def _load_v2_patch_file(self, output_dir: Path) -> list[dict[str, str]]:
        v2_patch_mappings: list[dict[str, str]] = []

        with self.v2_patch_file.open("rt") as f:
            for line in f:
                patch_mapping: dict[str, str] = json.loads(line)
                patch_mapping["source"] = str(output_dir / patch_mapping["source"])
                patch_mapping["destination"] = str(
                    output_dir / patch_mapping["destination"]
                )
                v2_patch_mappings.append(patch_mapping)

        return v2_patch_mappings


class Fruits360Dataset(ExampleDataset):
    """The Fruits 360 dataset hosted on Kaggle.

    Each image is stored as a 100x100 color JPG file and sorted into subdirectories
    according to their class label:

        Fruits360/
        ├── testing/
        │   ├── Apple Braeburn/
        │   ├── Apple Crimson Snow/
        │   ...
        └── training/
            ├── Apple Braeburn/
            ├── Apple Crimson Snow/
            ...

    Attributes:
        kaggle_dataset: The name of the Kaggle dataset.

    Args:
        remove_zip: If True, then delete the dataset zip file after extracting it.
            Defaults to True.

    Notes:
        You will need to register for a Kaggle account and obtain an API token in order
        to fetch the dataset using the Kaggle API. For instructions on how to obtain and
        use a Kaggle API token, see
        https://github.com/Kaggle/kaggle-api#api-credentials.

        Dataset URL: https://www.kaggle.com/datasets/moltean/fruits

    License:
        The Fruits 360 dataset is made available under the terms of the CC BY-SA 4.0
        license (https://creativecommons.org/licenses/by-sa/4.0/).
    """

    kaggle_dataset = "moltean/fruits"

    def __init__(self, remove_zip: bool = True) -> None:
        self._remove_zip = remove_zip

    def fetch(self, output_dir: str | Path, overwrite: bool = False) -> str:
        """Fetch the Fruits360 dataset.

        Args:
            output_path: The path to the folder where the example datasets are stored.
            overwrite: If True, fetch the Fruits360 data even if the target folder
                already exists and overwrite any existing data files.

        Returns:
            The path to the folder containing the Fruits360 dataset.

        Notes:
            Fetching the dataset using the Kaggle API requires the use of an API token.
            For instructions on how to obtain and use a Kaggle API token, see
            https://github.com/Kaggle/kaggle-api#api-credentials.
        """
        # fmt: off
        dataset_dir = Path(output_dir) / "Fruits360"
        zip_filepath = (
            (dataset_dir / self.kaggle_dataset.split("/")[-1]).with_suffix(".zip")
        )
        # fmt: on

        if dataset_dir.exists() and not overwrite:
            return str(dataset_dir)

        download_kaggle_dataset(
            dataset=self.kaggle_dataset,
            output_dir=dataset_dir,
            overwrite=overwrite,
            unzip=False,
        )
        unzip_kaggle_dataset(
            filepath=zip_filepath,
            output_dir=dataset_dir,
            namelist_filter=self._namelist_filter,
            remove_zip=self._remove_zip,
        )
        self._move_dirs(output_dir=dataset_dir)
        return str(dataset_dir)

    @staticmethod
    def _move_dirs(output_dir: Path):
        src_data_dir = output_dir / "fruits-360_dataset" / "fruits-360"

        src_training_dir = src_data_dir / "Training"
        dst_training_dir = output_dir / "training"
        src_training_dir.rename(dst_training_dir)

        src_testing_dir = src_data_dir / "Test"
        dst_testing_dir = output_dir / "testing"
        src_testing_dir.rename(dst_testing_dir)

        shutil.rmtree(src_data_dir.parent)

    @staticmethod
    def _namelist_filter(namelist: list[str]) -> list[str]:
        original_data_dir = Path("fruits-360_dataset") / "fruits-360"
        training_dir = original_data_dir / "Training"
        testing_dir = original_data_dir / "Test"

        return [
            x
            for x in namelist
            if Path(x).is_relative_to(training_dir)
            or Path(x).is_relative_to(testing_dir)
        ]


class ImageNetDataset(ExampleDataset):
    """The ImageNet Object Localization Challenge dataset hosted on Kaggle.

    This dataset uses a hybrid directory structure that combines the PascalVOC format
    with class label subdirectories to support both image classification and object
    detection tasks:

        ImageNet-Kaggle/
        ├── metadata/
        │   ├── image_sets/
        │   └── synset_mapping.txt
        ├── testing/
        │   ├── annotations/
        │   │   ├── n01440764/
        │   │   ├── n01443537/
        │   │   ...
        │   └── images/
        │       ├── n01440764/
        │       ├── n01443537/
        │       ...
        └── training/
            ├── annotations/
            │   ├── n01440764/
            │   ├── n01443537/
            │   ...
            └── images/
                ├── n01440764/
                ├── n01443537/
                ...

    Note:
        Because this data is for a competition, it is distributed with both a validation
        and a testing subset. The testing data does not come with labels, which is not
        useful in the examples. For this reason, the testing subset is dropped and the
        validation subset becomes the testing directory in the above schematic.

    To use the dataset for a classification task, use the training/images and
    testing/images folders and ignore the annotations folders. To use the dataset for an
    object detection task, ignore the synset subdirectories (e.g. n01440764).

    The metadata folder contains the following files that were also distributed as part
    of the competition:

    - The metadata/synset_mapping.txt file maps the 1000 synset ids to their
      human-readable descriptions.
    - The metadata/image_sets/ folder contains text files that specify lists of images
      used for the competition's main localization task.

    Todo:
        - Add synset subdirectories to the testing set folder to match the structure of
          the training folder. The testing folder is currently flat. The synset labels
          for the testing set can be obtained from the files in the annotations
          directory.
        - Test and confirm that the ImageNet fetching procedure works as expected.

    Attributes:
        kaggle_competition: The name of the Kaggle competition.

    Args:
        remove_zip: If True, then delete the dataset zip file after extracting it.
            Defaults to True.

    Notes:
        You will need to register for a Kaggle account and obtain an API token in order
        to fetch the dataset using the Kaggle API. For instructions on how to obtain and
        use a Kaggle API token, see
        https://github.com/Kaggle/kaggle-api#api-credentials.

        You will also need to login to your Kaggle account and accept the competition
        rules at https://www.kaggle.com/c/imagenet-object-localization-challenge/rules
        before you can download the dataset. You will receive a "403 Forbidden" error if
        you try to download the dataset without accepting the rules.

        Dataset URL: https://www.kaggle.com/c/imagenet-object-localization-challenge

    License:
        The ImageNet Object Localization Challenge dataset is available for use for
        non-commercial research and educational purposes only. For more information,
        read the Competition Framework section of the competition rules:
        https://www.kaggle.com/c/imagenet-object-localization-challenge/rules
    """

    kaggle_competition = "imagenet-object-localization-challenge"

    def __init__(self, remove_zip: bool = True) -> None:
        self._remove_zip = remove_zip

    def fetch(self, output_dir: str | Path, overwrite: bool = False) -> str:
        """Fetch the ImageNet dataset.

        Args:
            output_path: The path to the folder where the example datasets are stored.
            overwrite: If True, fetch the ImageNet data even if the target folder
                already exists and overwrite any existing data files.

        Returns:
            The path to the folder containing the ImageNet dataset.

        Notes:
            Fetching the dataset using the Kaggle API requires the use of an API token.
            For instructions on how to obtain and use a Kaggle API token, see
            https://github.com/Kaggle/kaggle-api#api-credentials.

            It is also necessary to accept the competition rules at
            https://www.kaggle.com/c/imagenet-object-localization-challenge/rules before
            fetching the dataset. Failing to accept the competition rules will result in
            a "403 Forbidden" error.
        """
        dataset_dir = Path(output_dir) / "ImageNet-Kaggle"
        zip_filepath = (dataset_dir / self.kaggle_competition).with_suffix(".zip")

        if dataset_dir.exists() and not overwrite:
            return str(dataset_dir)

        download_kaggle_competition(
            competition=self.kaggle_competition,
            output_dir=dataset_dir,
            overwrite=overwrite,
        )
        unzip_kaggle_dataset(
            filepath=zip_filepath,
            output_dir=dataset_dir,
            namelist_filter=self._namelist_filter,
            remove_zip=self._remove_zip,
        )
        self._move_dirs(output_dir=dataset_dir)
        self._add_synset_subdirs_to_testing_set(output_dir=dataset_dir)
        return str(dataset_dir)

    def _add_synset_subdirs_to_testing_set(self, output_dir: Path) -> None:
        # TODO: Implement method for adding synset subdirectories to the testing set
        # folder using the classification labels provided in the annotations directory.
        pass

    @staticmethod
    def _move_dirs(output_dir: Path):
        src_base_dir = output_dir / "ILSVRC"
        src_annotations_dir = src_base_dir / "Annotations" / "CLS-LOC"
        src_images_dir = src_base_dir / "Data" / "CLS-LOC"
        src_image_sets_dir = src_base_dir / "ImageSets" / "CLS-LOC"

        dst_training_dir = output_dir / "training"
        dst_testing_dir = output_dir / "testing"
        dst_metadata_dir = output_dir / "metadata"
        dst_training_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
        dst_testing_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
        dst_metadata_dir.mkdir(mode=0o755, parents=True, exist_ok=True)

        src_synset_mapping = Path("LOC_synset_mapping.txt")
        dst_synset_mapping = dst_metadata_dir / "synset_mapping.txt"
        src_synset_mapping.rename(dst_synset_mapping)

        src_training_annotations_dir = src_annotations_dir / "train"
        dst_training_annotations_dir = dst_training_dir / "annotations"
        src_training_annotations_dir.rename(dst_training_annotations_dir)

        src_validation_annotations_dir = src_annotations_dir / "val"
        dst_testing_annotations_dir = dst_testing_dir / "annotations"
        src_validation_annotations_dir.rename(dst_testing_annotations_dir)

        src_training_images_dir = src_images_dir / "train"
        dst_training_images_dir = dst_training_dir / "images"
        src_training_images_dir.rename(dst_training_images_dir)

        src_validation_images_dir = src_images_dir / "val"
        dst_testing_images_dir = dst_testing_dir / "images"
        src_validation_images_dir.rename(dst_testing_images_dir)

        dst_image_sets_dir = dst_metadata_dir / "image_sets"
        src_image_sets_dir.rename(dst_image_sets_dir)

        shutil.rmtree(src_base_dir.parent)

    @staticmethod
    def _namelist_filter(namelist: list[str]) -> list[str]:
        base_dir = Path("ILSVRC")
        testing_images_dir = base_dir / "Data" / "CLS-LOC" / "test"
        file_blacklist = {
            base_dir / "ImageSets" / "CLS-LOC" / "test.txt",
            Path("LOC_sample_submission.csv"),
            Path("LOC_train_solution.csv"),
            Path("LOC_val_solution.csv"),
        }

        return [
            x
            for x in namelist
            if not Path(x).is_relative_to(testing_images_dir)
            and Path(x) not in file_blacklist
        ]


class KaggleApi(object):
    """A wrapper for the Kaggle API command line tool.

    Args:
        cmd_path: The path to the Kaggle API command line tool executable. If not
            provided, then the class will try to find the executable automatically using
            the PATH environment variable and the location of the Python interpreter.

    Notes:
        A token is needed to access the Kaggle API. For instructions on how to obtain
        and use a Kaggle API token, see
        https://github.com/Kaggle/kaggle-api#api-credentials.
    """

    def __init__(self, cmd_path: Path | str | None = None) -> None:
        self._cmd_path = self._infer_kaggle_cmd_path(cmd_path)

    def call(self, *args: str) -> None:
        """Call the Kaggle API in a subprocess.

        Args:
            args: The arguments to pass to the Kaggle API command line tool.
        """
        cmd_args = [str(self._cmd_path), *args]
        subprocess.check_call(cmd_args)

    def download_competition(
        self,
        competition: str,
        output_path: str | None = None,
        force: bool = False,
    ) -> None:
        """Download the dataset for a Kaggle competition.

        Args:
            competition: The name of the competition.
            output_path: The path to the folder where the dataset should be
                stored. If not provided, then it will be stored in the current working
                directory.
            force: If True, then download the dataset even if it already exists.
                Defaults to False.
        """
        cmd_opts: list[str] = []

        if output_path is not None:
            cmd_opts.extend(["--path", output_path])

        if force:
            cmd_opts.append("--force")

        self.call("competitions", "download", *cmd_opts, competition)

    def download_dataset(
        self,
        dataset: str,
        output_path: str | None = None,
        unzip: bool = False,
        force: bool = False,
    ) -> None:
        """Download a Kaggle dataset.

        Args:
            dataset: The name of the dataset.
            output_path: The path to the folder where the dataset should be
                stored. If not provided, then it will be stored in the current working
                directory.
            unzip: If True, then unzip the dataset after downloading it and delete the
                zip file when completed. Defaults to False.
            force: If True, then download the dataset even if it already exists.
                Defaults to False.
        """
        cmd_opts: list[str] = []

        if output_path is not None:
            cmd_opts.extend(["--path", output_path])

        if unzip:
            cmd_opts.append("--unzip")

        if force:
            cmd_opts.append("--force")

        self.call("datasets", "download", *cmd_opts, dataset)

    @staticmethod
    def _infer_kaggle_cmd_path(cmd_path: Path | str | None) -> str:
        if cmd_path is not None and Path(cmd_path).exists():
            return str(cmd_path)

        if (cmd_path := shutil.which("kaggle")) is not None:
            return str(cmd_path)

        cmd_path = Path(sys.executable).parent / "kaggle"

        if cmd_path.exists():
            return str(cmd_path)

        raise RuntimeError("Unable to find kaggle command.")


def download_kaggle_competition(
    competition: str, output_dir: str | Path, overwrite: bool = False
) -> str:
    """Download the dataset for a Kaggle competition.

    Args:
        competition: The name of the competition.
        output_path: The path to the folder where the dataset should be stored.
        overwrite: If True, then download the dataset even if the target folder already
            exists and overwrite any existing files. Defaults to False.

    Returns:
        The path to the downloaded dataset.

    Notes:
        This function uses the Kaggle API and requires the use of an API token. For
        instructions on how to obtain and use a Kaggle API token, see
        https://github.com/Kaggle/kaggle-api#api-credentials.
    """
    kaggle_cmd = KaggleApi()
    output_dir = Path(output_dir)
    data_dir = output_dir.parent

    data_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=False, exist_ok=True)
    data_dir.chmod(0o755)
    output_dir.chmod(0o755)

    kaggle_cmd.download_competition(
        competition=competition, output_path=str(output_dir), force=overwrite
    )

    return str(output_dir)


def download_kaggle_dataset(
    dataset: str, output_dir: str | Path, overwrite: bool = False, unzip: bool = False
) -> str:
    """Download a Kaggle dataset.

    Args:
        dataset: The name of the dataset.
        output_path: The path to the folder where the dataset should be stored.
        overwrite: If True, then download the dataset even if the target folder already
            exists and overwrite any existing files. Defaults to False.
        unzip: If True, then unzip the dataset after downloading it and delete the zip
            file when completed. Defaults to False.

    Returns:
        The path to the downloaded dataset.

    Notes:
        This function uses the Kaggle API and requires the use of an API token. For
        instructions on how to obtain and use a Kaggle API token, see
        https://github.com/Kaggle/kaggle-api#api-credentials.
    """
    kaggle_cmd = KaggleApi()
    output_dir = Path(output_dir)

    output_dir.mkdir(mode=0o755, parents=True, exist_ok=True)

    kaggle_cmd.download_dataset(
        dataset=dataset, output_path=str(output_dir), unzip=unzip, force=overwrite
    )

    return str(output_dir)


def unzip_kaggle_dataset(
    filepath: str | Path,
    output_dir: str | Path,
    namelist_filter: Callable[[list[str]], list[str]] | None = None,
    remove_zip: bool = False,
) -> None:
    """Unzip a Kaggle dataset.

    Args:
        filepath: The path to the zip file that contains Kaggle dataset.
        output_dir: The path to the folder where the dataset should be extracted.
        namelist_filter: A function that takes a list of file paths in the zip file and
            returns a list of file paths that should be extracted. If not provided, then
            all files will be extracted.
        remove_zip: If True, then delete the zip file after extracting it. Defaults to
            False.
    """
    filepath = Path(filepath)
    output_dir = Path(output_dir)
    output_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
    filter_fn: Callable[[list[str]], list[str]] = namelist_filter or (lambda x: x)

    with zipfile.ZipFile(file=str(filepath), mode="r") as zip_file:
        zip_filelist: list[str] = filter_fn(zip_file.namelist())
        zip_file.extractall(path=str(output_dir), members=zip_filelist)

    if remove_zip:
        filepath.unlink()


def save_image(image_array: npt.NDArray[np.uint8], output_filepath: str | Path) -> None:
    """Save a numpy array as an image.

    Args:
        image_array: An 8-bit unsigned integer numpy array containing the image data.
        output_filepath: The path where the image should be saved. The file extension
            will be used to determine the image format.
    """
    output_filepath = Path(output_filepath)
    image: Image = Image.fromarray(image_array)
    image.save(f"{output_filepath}")
    output_filepath.chmod(0o644)


@click.group(context_settings=_CONTEXT_SETTINGS)
@click.option(
    "--output",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=Path.cwd(),
    help=(
        "The path to the folder where the example datasets are stored. Defaults to "
        "the current working directory."
    ),
)
@click.option(
    "--overwrite/--no-overwrite",
    type=click.BOOL,
    default=False,
    show_default=True,
    help=(
        "Fetch the data even if the target folder already exists and overwrite any "
        "existing data files. By default the program will exit early if the target "
        "folder already exists."
    ),
)
@click.pass_context
def download_data(ctx: Context, output: Path, overwrite: bool) -> None:
    """Fetch a dataset used in Dioptra's examples and demos."""
    # ensure that ctx.obj exists and is a dict (in case `cli()` is called
    # by means other than the `if` block below)
    ctx.ensure_object(dict)

    ctx.obj["Console"] = RichConsole(Console())
    ctx.obj["output"] = output.absolute()
    ctx.obj["overwrite"] = overwrite


@download_data.command()
@click.pass_context
def mnist(ctx: Context) -> None:
    """Fetch the MNIST dataset."""
    console: RichConsole = ctx.obj["Console"]
    output: Path = ctx.obj["output"]
    overwrite: bool = ctx.obj["overwrite"]

    console.print_title("Dioptra Examples - Data Downloader")
    console.print_parameter("Dataset", value="[default not bold]MNIST[/]")
    console.print_parameter("output", value=click.format_filename(output))
    console.print_parameter("overwrite", value=str(overwrite))

    console.print_info("[default not bold]Begin fetching the MNIST dataset.[/]")
    dataset = MnistDataset()
    dataset_path = dataset.fetch(output_dir=output, overwrite=overwrite)
    console.print_success(
        "[bold green]Success![/] [default not bold]Fetching of MNIST dataset is "
        "complete.[/]"
    )
    console.print_success(f"[yellow]Path:[/] {click.format_filename(dataset_path)}")


@download_data.command()
@click.pass_context
def roadsigns(ctx: Context) -> None:
    """Fetch the Road Signs Detection dataset hosted on Kaggle.

    This downloader uses the Kaggle API and requires the use of an API token. For
    instructions on how to obtain and use a Kaggle API token, see
    https://github.com/Kaggle/kaggle-api#api-credentials.
    """
    console: RichConsole = ctx.obj["Console"]
    output: Path = ctx.obj["output"]
    overwrite: bool = ctx.obj["overwrite"]

    console.print_title("Dioptra Examples - Data Downloader")
    console.print_parameter(
        "Dataset", value="[default not bold]Road Signs Detection[/]"
    )
    console.print_parameter("output", value=click.format_filename(output))
    console.print_parameter("overwrite", value=str(overwrite))

    console.print_info(
        "[default not bold]Begin fetching the Road Signs Detection dataset.[/]"
    )
    dataset = RoadSignsDataset()
    dataset_path = dataset.fetch(output_dir=output, overwrite=overwrite)
    console.print_success(
        "[bold green]Success![/] [default not bold]Fetching of Road Signs Detection "
        "dataset complete.[/]"
    )
    console.print_success(f"[yellow]Path:[/] {click.format_filename(dataset_path)}")


@download_data.command()
@click.option(
    "--remove-zip/--no-remove-zip",
    type=click.BOOL,
    default=True,
    help=(
        "Remove/keep the dataset zip file after extracting it. By default it will be "
        "removed."
    ),
)
@click.pass_context
def fruits360(ctx: Context, remove_zip: bool) -> None:
    """Fetch the Fruits 360 dataset hosted on Kaggle.

    This downloader uses the Kaggle API and requires the use of an API token. For
    instructions on how to obtain and use a Kaggle API token, see
    https://github.com/Kaggle/kaggle-api#api-credentials.
    """
    console: RichConsole = ctx.obj["Console"]
    output: Path = ctx.obj["output"]
    overwrite: bool = ctx.obj["overwrite"]

    console.print_title("Dioptra Examples - Data Downloader")
    console.print_parameter("Dataset", value="[default not bold]Fruits 360[/]")
    console.print_parameter("output", value=click.format_filename(output))
    console.print_parameter("overwrite", value=str(overwrite))
    console.print_parameter("remove-zip", value=str(remove_zip))

    console.print_info("[default not bold]Begin fetching the Fruits 360 dataset.[/]")
    dataset = Fruits360Dataset(remove_zip=remove_zip)
    dataset_path = dataset.fetch(output_dir=output, overwrite=overwrite)
    console.print_success(
        "[bold green]Success![/] [default not bold]Fetching of Fruits 360 "
        "dataset is complete.[/]"
    )
    console.print_success(f"[yellow]Path:[/] {click.format_filename(dataset_path)}")


@download_data.command()
@click.option(
    "--remove-zip/--no-remove-zip",
    type=click.BOOL,
    default=True,
    help=(
        "Remove/keep the dataset zip file after extracting it. By default it will be "
        "removed."
    ),
)
@click.pass_context
def imagenet(ctx: Context, remove_zip: bool) -> None:
    """Fetch the ImageNet Object Localization Challenge dataset hosted on Kaggle.

    ###########################################################################

    The ImageNet downloader is UNDER CONSTRUCTION and NOT AVAILABLE for use.
    Running it will print an alert and exit early.

    ###########################################################################

    This downloader uses the Kaggle API and requires the use of an API token. For
    instructions on how to obtain and use a Kaggle API token, see
    https://github.com/Kaggle/kaggle-api#api-credentials.

    It is also necessary to accept the competition rules at
    https://www.kaggle.com/c/imagenet-object-localization-challenge/rules before
    fetching the dataset. Failing to accept the competition rules will result in a "403
    Forbidden" error.
    """
    console: RichConsole = ctx.obj["Console"]
    output: Path = ctx.obj["output"]
    overwrite: bool = ctx.obj["overwrite"]

    console.print_title("Dioptra Examples - Data Downloader")
    console.print_parameter(
        "Dataset", value="[default not bold]ImageNet Object Localization Challenge[/]"
    )
    console.print_parameter("output", value=click.format_filename(output))
    console.print_parameter("overwrite", value=str(overwrite))
    console.print_parameter("remove-zip", value=str(remove_zip))

    # TODO: Delete alert when the ImageNet downloader is finished and ready for use.
    console.print_alert(
        "[default not bold]The ImageNet downloader is [yellow bold italic]under "
        "construction[/yellow bold italic] and [bold red italic]not "
        "available[/bold red italic] for use. Exiting...[/]"
    )

    # TODO: Uncomment when the ImageNet downloader is finished and ready for use.
    # console.print_info("[default not bold]Begin fetching of ImageNet dataset.[/]")
    # dataset = ImageNetDataset(remove_zip=remove_zip)
    # dataset_path = dataset.fetch(output_dir=output, overwrite=overwrite)
    # console.print_success(
    #     "[bold green]Success![/] [default not bold]Fetching of ImageNet dataset "
    #     "complete.[/]"
    # )
    # console.print_success(f"[yellow]Path:[/] {click.format_filename(dataset_path)}")


if __name__ == "__main__":
    download_data(obj={})
