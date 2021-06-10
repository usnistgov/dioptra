# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai.restapi.models import TaskPlugin
from mitre.securingai.restapi.task_plugin.interface import TaskPluginInterface

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def test_TaskPluginInterface_create(
    new_task_plugin_interface: TaskPluginInterface,
) -> None:
    assert isinstance(new_task_plugin_interface, dict)


def test_TaskPluginInterface_works(
    new_task_plugin_interface: TaskPluginInterface,
) -> None:
    task_plugin: TaskPlugin = TaskPlugin(**new_task_plugin_interface)
    assert isinstance(task_plugin, TaskPlugin)
