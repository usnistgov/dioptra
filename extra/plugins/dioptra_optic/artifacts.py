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
import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

import keras
import structlog
import tensorflow as tf
from structlog.stdlib import BoundLogger

from dioptra.sdk.api.artifact import ArtifactTaskInterface

from .data import Dataset, DatasetMetadata

LOGGER: BoundLogger = structlog.stdlib.get_logger()


class KerasModelArtifactTask(ArtifactTaskInterface):
    @staticmethod
    def serialize(
        working_dir: Path, name: str, contents: keras.Model, **kwargs
    ) -> Path:
        result = (working_dir / name).with_suffix(".keras")
        contents.save(result, **kwargs)
        return result

    @staticmethod
    def deserialize(working_dir: Path, path: str, **kwargs) -> Any:
        return keras.saving.load_model(Path(working_dir) / path, **kwargs)

    @staticmethod
    def validation() -> dict[str, Any] | None:
        return None


class DatasetArtifactTask(ArtifactTaskInterface):
    @staticmethod
    def serialize(working_dir: Path, name: str, contents: Dataset, **kwargs) -> Path:
        """
        Serializes a Dataset to disk.
        """

        # if the Dataset has a name, it represents a directory path to an already serialized dataset
        dataset_name = contents.data.options().dataset_name
        if dataset_name and (working_dir / dataset_name).exists():
            os.symlink(working_dir / dataset_name, working_dir / name)
        elif isinstance(contents, Dataset):
            contents.data.save(str(working_dir / name), **kwargs)
            with open(working_dir / name / "metadata.json", "w") as f:
                json.dump(asdict(contents.meta), f)

        return working_dir / name

    @staticmethod
    def deserialize(working_dir: Path, path: str, **kwargs) -> Dataset:
        data = tf.data.Dataset.load(str(working_dir / path), **kwargs)
        with open(working_dir / path / "metadata.json", "rb") as f:
            meta = DatasetMetadata(**json.load(f))
        return Dataset(data=data, meta=meta)

    @staticmethod
    def validation() -> dict[str, Any] | None:
        return None


class DatasetSamplerArtifactTask(ArtifactTaskInterface):
    @staticmethod
    def serialize(
        working_dir: Path,
        name: str,
        contents: "Dataset",
        num_samples: int = 32,
        seed: int | None = 42,
        **kwargs,
    ) -> Path:
        output_dir = working_dir / name
        output_dir.mkdir(parents=True, exist_ok=True)

        data = contents.data.shuffle(num_samples, seed=seed).unbatch()
        for idx, (x, y) in data.take(num_samples).enumerate():
            y = keras.ops.argmax(y, axis=0)
            keras.utils.save_img(
                output_dir / f"{idx:06d}_label_{y:04d}.png", x.numpy(), **kwargs
            )
        return output_dir

    @staticmethod
    def deserialize(working_dir: Path, path: str, **kwargs) -> Path:
        return working_dir / path

    @staticmethod
    def validation() -> dict[str, Any] | None:
        return None
