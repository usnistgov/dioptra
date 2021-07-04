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
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Union

from testinfra.host import Host

PathLike = List[Union[str, Path]]


@dataclass
class TestbedHosts(object):
    minio: Host
    mlflow_tracking: Host
    nginx: Host
    redis: Host
    restapi: Host
    tfcpu_01: Host


def initialize_minio(
    compose_file: PathLike,
    minio_endpoint_alias: str,
    minio_root_user: str,
    minio_root_password: str,
    plugins_builtins_dir: str,
) -> None:
    subprocess.check_call(
        f'docker-compose -f {compose_file} run --rm mc -c "'
        f"mc alias set {minio_endpoint_alias} http://minio:9000 "
        f"{minio_root_user} {minio_root_password} && mc mb "
        f"{minio_endpoint_alias}/plugins {minio_endpoint_alias}/workflow && "
        f"mc mirror --overwrite --remove /task-plugins/{plugins_builtins_dir}/ "
        f"{minio_endpoint_alias}/plugins/{plugins_builtins_dir}"
        '"',
        shell=True,
    )
