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
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import click
import numpy as np
import pandas as pd
import requests
from PIL import Image
from rich.console import Console
from rich.panel import Panel

CONSOLE: Console = Console()


class AppConsole(object):
    def __init__(self, console: Console) -> None:
        self._console = console

    def print_alert(self, text: str) -> None:
        content: str = f":heavy_exclamation_mark: {text}"
        self._console.print(content)

    def print_failure(self, text: str) -> None:
        content: str = f":x:  {text}"
        self._console.print(content)

    def print_info(self, text: str) -> None:
        content: str = f"[bold yellow]Ⓘ[/bold yellow]  {text}"
        self._console.print(content)

    def print_parameter(self, name: str, value: str) -> None:
        content: str = f" ‣ [bold]{name}:[/bold] {value}"
        self._console.print(content)

    def print_success(self, text: str) -> None:
        content: str = f" [bold bright_green]✔[/bold bright_green] {text}"
        self._console.print(content)

    def print_title(self, text: str) -> None:
        content: Panel = Panel(renderable=text, expand=False)
        self._console.print(content, style="bold cyan")

    def print_warning(self, text: str) -> None:
        content: str = f":warning: {text}"
        self._console.print(content)


class MnistDataset(object):
    """Adapter class for accessing the MNIST dataset.

    This class will check if a copy of the MNIST dataset is in a caching directory. If
    it exists, then it will be used to load the training and testing datasets. If it
    doesn't, then it will be downloaded using the `data_url` attribute URL.

    Attributes:
        data_url: A URL pointing to a downloadable copy the MNIST dataset.

    License:
        Yann LeCun and Corinna Cortes hold the copyright of MNIST dataset, which is a
        derivative work from original NIST datasets. MNIST dataset is made available
        under the terms of the `Creative Commons Attribution-Share Alike 3.0 license
        <https://creativecommons.org/licenses/by-sa/3.0/>`_.
    """

    data_url = "https://storage.googleapis.com/tensorflow/tf-keras-datasets/mnist.npz"

    def __init__(self, cache_dir: str) -> None:
        self._train_images_cache: Optional[np.ndarray] = None
        self._train_labels_cache: Optional[np.ndarray] = None
        self._test_images_cache: Optional[np.ndarray] = None
        self._test_labels_cache: Optional[np.ndarray] = None
        self._cache_dir: str = cache_dir

    @property
    def data_file(self) -> str:
        return self._download_mnist_file(
            url=self.data_url,
            output_path=Path(self._cache_dir) / "mnist.npz",
        )

    @property
    def train_images_cache(self) -> np.ndarray:
        if self._train_images_cache is None:
            with np.load(self.data_file, allow_pickle=True) as f:  # type: ignore[no-untyped-call] # noqa: B950
                self._train_images_cache = f["x_train"]

        return self._train_images_cache

    @property
    def train_labels_cache(self) -> np.ndarray:
        if self._train_labels_cache is None:
            with np.load(self.data_file, allow_pickle=True) as f:  # type: ignore[no-untyped-call] # noqa: B950
                self._train_labels_cache = f["y_train"]

        return self._train_labels_cache

    @property
    def test_images_cache(self) -> np.ndarray:
        if self._test_images_cache is None:
            with np.load(self.data_file, allow_pickle=True) as f:  # type: ignore[no-untyped-call] # noqa: B950
                self._test_images_cache = f["x_test"]

        return self._test_images_cache

    @property
    def test_labels_cache(self) -> np.ndarray:
        if self._test_labels_cache is None:
            with np.load(self.data_file, allow_pickle=True) as f:  # type: ignore[no-untyped-call] # noqa: B950
                self._test_labels_cache = f["y_test"]

        return self._test_labels_cache

    @property
    def training(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "id": range(len(self.train_images_cache)),
                "image": [image_array for image_array in self.train_images_cache],
                "label": [label for label in self.train_labels_cache],
            }
        )

    @property
    def testing(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "id": range(len(self.test_images_cache)),
                "image": [image_array for image_array in self.test_images_cache],
                "label": [label for label in self.test_labels_cache],
            }
        )

    @staticmethod
    def _download_mnist_file(url: str, output_path: Path) -> str:
        if output_path.exists():
            return str(output_path)

        mnist_npz = requests.get(url=url)

        with output_path.open("wb") as f:
            f.write(mnist_npz.content)

        return str(output_path)


def save_gif_images(
    dataset: pd.DataFrame, target_dir: Path, subsample_size: int, seed: int = 22009
) -> None:
    subsample_dataset: pd.DataFrame = dataset.groupby("label").sample(
        n=subsample_size, random_state=seed
    )

    for image_id, image_array, image_label in subsample_dataset.itertuples(index=False):
        image: Image = Image.fromarray(image_array)
        image_filepath: Path = (
            target_dir / f"{image_label}" / f"{str(image_id).zfill(5)}.png"
        )

        if not image_filepath.parent.exists():
            image_filepath.parent.mkdir(parents=True, exist_ok=True)
            image_filepath.parent.chmod(0o777)

        image.save(f"{image_filepath}")


@click.command()
@click.option(
    "--cache-dir",
    type=click.Path(),
    help="Caching directory",
)
@click.option(
    "--data-dir",
    type=click.Path(),
    help="Save dataset in this directory",
)
@click.option(
    "--subsample-size",
    type=click.INT,
    default=10,
    help="Sets the number of images to sample per unique label",
)
@click.option(
    "--seed",
    type=click.INT,
    default=22009,
    help="Random seed for reproducibility",
)
def download_data(
    cache_dir: Union[str, Path], data_dir: str, subsample_size: int, seed: int
) -> None:
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.chmod(0o777)

    console: AppConsole = AppConsole(CONSOLE)
    mnist_dataset: MnistDataset = MnistDataset(str(cache_dir))

    console.print_title("MNIST Data Downloader")
    console.print_parameter(
        "cache-dir", value=f"{click.format_filename(str(cache_dir))}"
    )
    console.print_parameter("data-dir", value=f"{click.format_filename(data_dir)}")
    console.print_parameter("subsample-size", value=str(subsample_size))

    target_dir: Path = Path(data_dir) / "training"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_dir.chmod(0o777)
    console.print_info("Begin download of MNIST training dataset")
    save_gif_images(
        dataset=mnist_dataset.training,
        target_dir=target_dir,
        subsample_size=subsample_size,
        seed=seed,
    )
    console.print_success("Training images downloaded")
    console.print_info("MNIST training dataset downloading complete")

    target_dir = Path(data_dir) / "testing"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_dir.chmod(0o777)
    console.print_info("Begin download of MNIST testing dataset")
    save_gif_images(
        dataset=mnist_dataset.testing,
        target_dir=target_dir,
        subsample_size=subsample_size,
        seed=seed + 1,
    )
    console.print_success("Testing images downloaded")
    console.print_info("MNIST testing dataset downloading complete")


if __name__ == "__main__":
    download_data()
