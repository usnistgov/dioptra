from __future__ import annotations

from pathlib import Path

import pytest

from dioptra.sdk.utilities.contexts import plugin_dirs

TASK_PLUGINS_DIR = (Path(__file__).parent / ".." / ".." / ".." / "task-plugins").resolve()


@pytest.fixture(scope="session", autouse=True)
def plugin_dirs_context():
    with plugin_dirs([TASK_PLUGINS_DIR]):
        yield
