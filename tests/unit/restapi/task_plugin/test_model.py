# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
import structlog
from structlog.stdlib import BoundLogger

from mitre.securingai.restapi.models import (
    TaskPlugin,
    TaskPluginUploadForm,
    TaskPluginUploadFormData,
)

LOGGER: BoundLogger = structlog.stdlib.get_logger()


def test_TaskPlugin_create(new_task_plugin: TaskPlugin) -> None:
    assert isinstance(new_task_plugin, TaskPlugin)


def test_TaskPluginUploadForm_create(
    task_plugin_upload_form: TaskPluginUploadForm,
) -> None:
    assert isinstance(task_plugin_upload_form, TaskPluginUploadForm)


def test_TaskPluginUploadFormData_create(
    task_plugin_upload_form_data: TaskPluginUploadFormData,
) -> None:
    assert isinstance(task_plugin_upload_form_data, dict)
