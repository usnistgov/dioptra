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
"""Job workspace paths and bundle/file handling."""

import json
import tarfile
from pathlib import Path
from typing import Any, Mapping, cast

import yaml
from structlog.stdlib import BoundLogger


class Context(object):
    def __init__(self) -> None:
        self.working_dir = Path().resolve()
        self.dioptra_dir = self.working_dir / ".dioptra"
        self.serialize_dir = self.dioptra_dir / "serialize"
        self.deserialize_dir = self.dioptra_dir / "deserialize"
        self.plugins_dir = self.dioptra_dir / "plugins"
        self.artifacts_dir = self.dioptra_dir / "artifacts"

        self.parameters_file = self.working_dir / "parameters.json"
        self.artifact_parameters_file = self.working_dir / "artifact_parameters.json"
        self.args_file = self.dioptra_dir / "args.json"
        self.artifacts_results_file = self.dioptra_dir / "artifacts.json"
        self.artifact_plugins_file = self.serialize_dir / "artifact_plugins.json"
        self.artifact_tasks_file = self.serialize_dir / "artifact_tasks.json"

    def yaml_path(self, entrypoint_name: str) -> Path:
        return Path(self.working_dir, f"{entrypoint_name}.yml")

    def mkdirs(self) -> None:
        # make the directories if needed
        self.dioptra_dir.mkdir(exist_ok=True)
        self.serialize_dir.mkdir(exist_ok=True)
        self.deserialize_dir.mkdir(exist_ok=True)
        self.plugins_dir.mkdir(exist_ok=True)
        self.artifacts_dir.mkdir(exist_ok=True)


def save_job_yaml(filepath: Path, job_yaml: Mapping[str, Any]) -> None:
    with filepath.open("wt") as f:
        yaml.safe_dump(data=job_yaml, stream=f)


def load_job_yaml(filepath: Path) -> Mapping[str, Any]:
    with filepath.open("rt") as f:
        return cast(Mapping[str, Any], yaml.safe_load(f))


def save_as_json(filepath: Path, params: Any) -> None:
    with filepath.open("wt") as f:
        json.dump(obj=params, fp=f)


def load_json(filepath: Path) -> Any:
    with filepath.open("rt") as f:
        return json.load(f)


def unpack(source: Path, dest: Path, log: BoundLogger) -> None:
    # Unpack the (trusted) tar.gz file
    try:
        with tarfile.open(source, mode="r:*") as tar:
            tar.extractall(path=dest, filter="data")
    except Exception as e:
        log.exception(f"Could not extract from tar file {source.as_posix()}")
        raise e


def save_args(
    filepath: Path, job_id: int, experiment_id: int, entrypoint_name: str
) -> None:
    save_as_json(
        filepath=filepath,
        params={
            "job_id": job_id,
            "experiment_id": experiment_id,
            "entrypoint_name": entrypoint_name,
        },
    )
