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

import json
import os
import shutil
import zipfile
from functools import partial
from pathlib import Path

import click
import pandas as pd
import requests
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


class RoadSignsDataset(object):
    """Adapter class for accessing the Road Signs dataset.

    This class will check if an original copy of the Road Signs dataset is available.
    Users can choose to upgrade the dataset to use the updated annotations, filenames,
    and a predetermined train/test split.

    Attributes:
        data_url: A URL pointing to a downloadable copy of the Road Signs dataset.
        output_folder: The folder where the downloaded data will be unpacked.
        v2_upgrade_file: The full path to a jsonlines file containing the filename
            mappings needed to upgrade the dataset

    License:
        Public Domain
    """

    data_url = "https://arcraftimages.s3-accelerate.amazonaws.com/Datasets/RoadSigns/RoadSignsPascalVOC.zip"  # noqa: B950
    output_folder = "RoadSignsPascalVOC"
    v2_upgrade_file = str(
        Path(__file__).parent.resolve() / "road_signs_dataset_v2_upgrade.jsonl"
    )

    def __init__(self, output_dir: str | Path | None = None) -> None:
        self._output_dir = Path(output_dir) if output_dir is not None else None
        self._v2_upgrade: str | None = None

    @property
    def annotations(self) -> str:
        filepath = Path(self.output_dir) / self.output_folder / "annotations"

        return str(filepath)

    @property
    def downloaded_files(self) -> list[str]:
        annotation_files: list[str] = [
            str(x) for x in Path(self.annotations).glob("*.xml")
        ]
        image_files: list[str] = [str(x) for x in Path(self.images).glob("*.png")]
        downloaded_files: list[str] = annotation_files + image_files

        return downloaded_files

    @property
    def data_file(self) -> str:
        return self._download_file(
            url=self.data_url,
            output_path=Path(self.output_dir) / "RoadSignsPascalVOC.zip",
        )

    @property
    def images(self) -> pd.DataFrame:
        filepath = Path(self.output_dir) / self.output_folder / "images"

        return str(filepath)

    @property
    def output_dir(self) -> str:
        if self._output_dir is None:
            self._output_dir = Path.cwd()

        if not self._output_dir.exists():
            self._output_dir.mkdir(mode=0o755, parents=True)

        return str(self._output_dir)

    @property
    def v2_upgrade_info(self) -> list[dict[str, str]]:
        if self._v2_upgrade is None:
            self._v2_upgrade = self._read_dataset_v2_upgrade_info()

        return self._v2_upgrade

    def cleanup(self) -> None:
        target_dir = Path(self.output_dir) / self.output_folder
        zip_filepath = Path(self.output_dir) / "RoadSignsPascalVOC.zip"

        shutil.rmtree(path=target_dir)
        os.unlink(path=zip_filepath)

    def extract(self) -> None:
        target_dir = Path(self.output_dir) / self.output_folder
        downloaded_files: set[str] = set(self.downloaded_files)

        if not target_dir.exists():
            target_dir.mkdir(mode=0o755, parents=True)

        with zipfile.ZipFile(file=self.data_file, mode="r") as zip_file:
            zip_filelist: list[str] = [
                x
                for x in zip_file.namelist()
                if not x.startswith("__MACOSX") and x not in downloaded_files
            ]
            zip_file.extractall(path=target_dir, members=zip_filelist)

    def upgrade(self):
        for upgrade_mapping in self.v2_upgrade_info:
            destination_dir = Path(upgrade_mapping["destination"]).parent

            if not destination_dir.exists():
                destination_dir.mkdir(mode=0o755, parents=True)

            shutil.copy(
                src=upgrade_mapping["source"],
                dst=upgrade_mapping["destination"],
            )

    def _read_dataset_v2_upgrade_info(self) -> list[dict[str, str]]:
        dataset_v2_upgrade: list[dict[str, str]] = []

        with open(self.v2_upgrade_file, "rt") as f:
            for line in f:
                upgrade_mapping: dict[str, str] = json.loads(line)
                upgrade_mapping["source"] = str(
                    Path(self.output_dir).resolve() / upgrade_mapping["source"]
                )
                upgrade_mapping["destination"] = str(
                    Path(self.output_dir).resolve() / upgrade_mapping["destination"]
                )
                dataset_v2_upgrade.append(upgrade_mapping)

        return dataset_v2_upgrade

    @staticmethod
    def _download_file(url: str, output_path: Path) -> str:
        if output_path.exists():
            return str(output_path)

        with requests.get(url=url, stream=True) as response:
            response.raise_for_status()
            response.raw.read = partial(response.raw.read, decode_content=True)

            with output_path.open("wb") as f:
                shutil.copyfileobj(response.raw, f)

        return str(output_path)


@click.command()
@click.option(
    "--data-dir",
    type=click.Path(),
    help="Save dataset in this directory",
)
@click.option(
    "--upgrade/--no-upgrade",
    default=True,
    help="Upgrade the dataset after downloading and unpacking it",
    show_default=True,
)
@click.option(
    "--clean/--no-clean",
    default=False,
    help=(
        "Remove the downloaded zip file and original files after upgrading "
        "(--upgrade only)"
    ),
    show_default=True,
)
def download_roadsigns_data(data_dir: str, upgrade: bool, clean: bool) -> None:
    console: AppConsole = AppConsole(CONSOLE)
    road_signs_dataset: RoadSignsDataset = RoadSignsDataset(str(data_dir))

    console.print_title("Road Signs Dataset Downloader")
    console.print_parameter("data-dir", value=f"{click.format_filename(data_dir)}")
    console.print_parameter("upgrade", value=f"{upgrade}")
    console.print_parameter("clean", value=f"{clean}")

    console.print_info("Begin download of Road Signs dataset")
    road_signs_dataset.extract()
    console.print_info("Downloading complete")

    if upgrade:
        console.print_info("Begin v2 upgrade of Road Signs dataset")
        road_signs_dataset.upgrade()
        console.print_info("Upgrading complete")

    if upgrade and clean:
        console.print_info("Begin post-upgrade cleanup")
        road_signs_dataset.cleanup()
        console.print_info("Cleanup complete")

    elif not upgrade and clean:
        console.print_info("Dataset was not upgraded, skipping cleanup")


if __name__ == "__main__":
    download_roadsigns_data()
