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

from pathlib import Path
from typing import Optional, Union

import click
import mnist
import numpy as np
import pandas as pd
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
    train_images = "train-images-idx3-ubyte.gz"
    train_labels = "train-labels-idx1-ubyte.gz"
    test_images = "t10k-images-idx3-ubyte.gz"
    test_labels = "t10k-labels-idx1-ubyte.gz"

    def __init__(self, cache_dir: Optional[str] = None) -> None:
        self._train_images_cache: Optional[np.ndarray] = None
        self._train_labels_cache: Optional[np.ndarray] = None
        self._test_images_cache: Optional[np.ndarray] = None
        self._test_labels_cache: Optional[np.ndarray] = None
        self._cache_dir: Optional[str] = cache_dir

    @property
    def training(self) -> pd.DataFrame:
        if self._train_images_cache is None:
            self._train_images_cache = mnist.download_and_parse_mnist_file(
                fname=self.train_images,
                target_dir=self._cache_dir,
            )

        if self._train_labels_cache is None:
            self._train_labels_cache = mnist.download_and_parse_mnist_file(
                fname=self.train_labels,
                target_dir=self._cache_dir,
            )

        return pd.DataFrame(
            {
                "id": range(len(self._train_labels_cache)),
                "image": [image_array for image_array in self._train_images_cache],
                "label": [label for label in self._train_labels_cache],
            }
        )

    @property
    def testing(self) -> pd.DataFrame:
        if self._test_images_cache is None:
            self._test_images_cache = mnist.download_and_parse_mnist_file(
                fname=self.test_images,
                target_dir=self._cache_dir,
            )

        if self._test_labels_cache is None:
            self._test_labels_cache = mnist.download_and_parse_mnist_file(
                fname=self.test_labels,
                target_dir=self._cache_dir,
            )

        return pd.DataFrame(
            {
                "id": range(len(self._test_labels_cache)),
                "image": [image_array for image_array in self._test_images_cache],
                "label": [label for label in self._test_labels_cache],
            }
        )


def save_gif_images(dataset: pd.DataFrame, target_dir: Path) -> None:
    for image_id, image_array, image_label in dataset.itertuples(index=False):
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
    "--training/--no-training",
    default=False,
    help="Download and prepare MNIST training data set",
)
@click.option(
    "--testing/--no-testing",
    default=False,
    help="Download and prepare MNIST testing data set",
)
@click.option(
    "--cache-dir",
    type=click.Path(),
    default=f"{Path(__file__).parent}/.cache",
    help="Caching directory",
)
@click.option(
    "--data-dir",
    type=click.Path(),
    default=f"{Path(__file__).parent}",
    help="Save dataset in this directory",
)
def download_data(
    training: bool, testing: bool, cache_dir: Union[str, Path], data_dir: str
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

    if training:
        target_dir: Path = Path(data_dir) / "training"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_dir.chmod(0o777)
        console.print_info("Begin download of MNIST training dataset")
        save_gif_images(dataset=mnist_dataset.training, target_dir=target_dir)
        console.print_success("Training images downloaded")
        console.print_info("MNIST training dataset downloading complete")

    if testing:
        target_dir = Path(data_dir) / "testing"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_dir.chmod(0o777)
        console.print_info("Begin download of MNIST testing dataset")
        save_gif_images(dataset=mnist_dataset.testing, target_dir=target_dir)
        console.print_success("Testing images downloaded")
        console.print_info("MNIST testing dataset downloading complete")


if __name__ == "__main__":
    download_data()
