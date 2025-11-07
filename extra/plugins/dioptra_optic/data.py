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
# https://creativecommons.org/licenses/by/4.0/legalcodefrom typing import Literal
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

import structlog
import tensorflow as tf
import tensorflow_datasets as tfds

from dioptra import pyplugs

LOGGER = structlog.get_logger()


@dataclass
class DatasetMetadata:
    split: dict[Literal["train", "val", "test"]]
    normalize_val: float
    image_size: tuple[int, int]
    batch_size: int
    num_classes: int


@pyplugs.register
def load_dataset_from_tfds(
    name: str,
    split: dict[Literal["train", "val", "test"], str] | None = None,
    data_dir: str = "/dioptra/data",
    normalize_val: float | None = 255.0,
    image_size: tuple[int, int] | None = None,
    batch_size: int = 32,
    shuffle_buffer_size: int = 10000,
    seed: int | None = None,
) -> tuple[
    tf.data.Dataset | None,
    tf.data.Dataset | None,
    tf.data.Dataset | None,
    DatasetMetadata,
]:
    """
    Loads a registered tfds dataset by name from disk and constructs a preprocessing pipeline.

    Args:
        name: The name of the dataset registered in tfds
        See `_load_dataset_from_builder` for description of arguments

    Returns:
        A tuple of train, val, test tf.data.Dataset objects.
    """
    split = split or {
        "train": "train[:80%]",
        "val": "train[80%:]",
        "test": "test",
    }

    builder = tfds.builder(name, data_dir=data_dir)
    return _load_dataset_from_builder(
        builder,
        split=split,
        normalize_val=normalize_val,
        image_size=image_size,
        batch_size=batch_size,
        shuffle_buffer_size=shuffle_buffer_size,
        seed=seed,
    )


@pyplugs.register
def load_dataset_from_image_directory(
    data_dir: Path,
    split: dict[Literal["train", "val", "test"], str] | None = None,
    normalize_val: float | None = 255.0,
    image_size: tuple[int, int] | None = None,
    batch_size: int = 32,
    shuffle_buffer_size: int = 10000,
    seed: int | None = None,
) -> tuple[
    tf.data.Dataset | None,
    tf.data.Dataset | None,
    tf.data.Dataset | None,
    DatasetMetadata,
]:
    """
    Loads a tfds dataset by path from disk and constructs a preprocessing pipeline.

    Args:
        data_dir: The path to the directory containing the image dataset
        See `_load_dataset_from_builder` for description of arguments

    Returns:
        A tuple of train, val, test tf.data.Dataset objects.
    """
    split = split or {
        "train": "train[:80%]",
        "val": "train[80%:]",
        "test": "test",
    }

    builder = tfds.ImageFolder(str(data_dir))
    return _load_dataset_from_builder(
        builder,
        split=split,
        normalize_val=normalize_val,
        image_size=image_size,
        batch_size=batch_size,
        shuffle_buffer_size=shuffle_buffer_size,
        seed=seed,
    )


def _load_dataset_from_builder(
    builder: tfds.core.DatasetBuilder,
    split: dict[Literal["train", "val", "test"], str] | None = None,
    normalize_val: float | None = 255.0,
    image_size: tuple[int, int] | None = None,
    batch_size: int = 32,
    shuffle_buffer_size: int = 10000,
    seed: int | None = None,
) -> tuple[
    tf.data.Dataset | None,
    tf.data.Dataset | None,
    tf.data.Dataset | None,
    DatasetMetadata,
]:
    """
    Args:
        builder: A tfds.core.DatasetBuilder to build the dataset from.
        split: A tuple denoting the train/val/test split for the dataset.
            See https://www.tensorflow.org/datasets/splits
        normalize_val: The data is normalized by dividing by this value.
            If None, no data normalization is applied
        image_size: Size to
            If None, no resizing is applied.
        batch_size: Applies batching to the dataset with the specified size.
            If None, no batching is applied.
        shuffle_buffer_size: The number of data samples to use in the shuffle buffer,
            see https://www.tensorflow.org/api_docs/python/tf/data/Dataset#shuffle
        seed: The random seed used to shuffle the train split. Used for deterministic results.
            If None, shuff

    Returns:
        A tuple of train, val, test tf.data.Dataset objects.
    """
    split = split or {
        "train": "train[:80%]",
        "val": "train[80%:]",
        "test": "test",
    }

    # get a dictionary of dataset splits from the builder
    dataset: dict = builder.as_dataset(split=split, as_supervised=True)

    num_classes = builder.info.features["label"].num_classes

    def normalize(x, y):
        """Normalizes images: `uint8` -> `float32`."""
        return tf.cast(x, tf.float32) / tf.cast(normalize_val, tf.float32), y

    def resize(x, y):
        """Resizes images"""
        return tf.image.resize(x, image_size), y

    def one_hot(x, y):
        """Converts categorical labels to one-hot vectors."""
        return x, tf.one_hot(y, num_classes)

    # setup train/val/test data pipelines
    # following the guidance for ordering of cache, shuffle, and batch operations from:
    # https://www.tensorflow.org/datasets/keras_example
    for name, ds in dataset.items():
        ds = ds.map(one_hot, num_parallel_calls=tf.data.AUTOTUNE)
        if normalize_val is not None:
            ds = ds.map(normalize, num_parallel_calls=tf.data.AUTOTUNE)
        if image_size is not None:
            ds = ds.map(resize, num_parallel_calls=tf.data.AUTOTUNE)

        if name == "train":
            buffer_size = max(ds.cardinaliy().numpy(), shuffle_buffer_size)
            ds = ds.cache()
            ds = ds.shuffle(buffer_size, seed=seed, reshuffle_each_iteration=True)
            ds = ds.batch(batch_size)
        else:
            ds = ds.batch(batch_size)
            ds = ds.cache()
        ds = ds.prefetch(tf.data.AUTOTUNE)

        dataset[name] = ds

    metadata = DatasetMetadata(
        split=split,
        normalize_val=normalize_val or 1.0,
        image_size=image_size or builder.info.features["image"].shape[:2],
        batch_size=batch_size,
        num_classes=num_classes,
    )

    return (
        dataset.get("train", None),
        dataset.get("val", None),
        dataset.get("test", None),
        metadata,
    )


def create_transformed_dataset(
    dataset: tf.data.Dataset,
    fn: Callable[[tf.Tensor, tf.Tensor], tuple[tf.Tensor, tf.Tensor]],
    save_dataset: bool = False,
):
    """
    Maps the provided function to the dataset to create a transformed dataset.

    If `save_dataset` is True, the dataset is saved to disk then re-constituted from that location.
    This effectively caches the transformation to disk. The dataset is saved to a directory with a
    random uuid4. This uuid is stored in the dataset_name field of the dataset options.

    Note that if `save_dataset` is False, the transformation is not actually performed because map
    is not executed eagerly.

    Additionally maps `set_shape` to avoid unknown rank errors.

    Args:
        dataset: The dataset to be transformed.
        fn: The function used to transform the dataset.
            See https://www.tensorflow.org/api_docs/python/tf/data/Dataset#map
        save_dataset: Whether to save the dataset to disk.

    Returns:
        The transformed tf.data.Dataset
    """

    def set_shape(x, y):
        x.set_shape(x.shape)
        return x, y

    dataset = dataset.map(fn, num_parallel_calls=tf.data.AUTOTUNE, deterministic=True)
    dataset = dataset.map(
        set_shape, num_parallel_calls=tf.data.AUTOTUNE, deterministic=True
    )

    if save_dataset:
        options = tf.data.Options().merge(dataset.options())
        options.dataset_name = str(uuid.uuid4())

        dataset.save(options.dataset_name)

        # reload from disk to prevent repeat computation
        dataset = tf.data.Dataset.load(options.dataset_name).with_options(options)

    return dataset
