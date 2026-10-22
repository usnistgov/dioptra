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
import os
import re
import runpy
from pathlib import Path

import pytest
from binaryornot.check import is_binary

PATTERN = r"{{(\s?cookiecutter)[.](.*?)}}"
RE_OBJ = re.compile(PATTERN)


# Source: https://github.com/cookiecutter/cookiecutter-django/blob/f8897bfdff9681a28bc07b3361ab51bddb71a27c/tests/test_cookiecutter_generation.py
def check_paths(paths):
    """Method to check all paths have correct substitutions."""
    # Assert that no match is found in any of the files
    for path in paths:
        if is_binary(str(path)):
            continue

        for line in path.open("r", encoding="utf-8"):
            match = RE_OBJ.search(line)
            assert match is None, f"cookiecutter variable not replaced in {path}"


# Source: https://github.com/cookiecutter/cookiecutter-django/blob/f8897bfdff9681a28bc07b3361ab51bddb71a27c/tests/test_cookiecutter_generation.py
def build_files_list(root_dir):
    """Build a list containing absolute paths to the generated files."""
    return [
        Path(dirpath) / file_path
        for dirpath, _, files in os.walk(root_dir)
        for file_path in files
    ]


def check_temp_paths_are_removed(result):
    temp_paths = [
        result.project_path / "templates",
    ]

    for temp_path in temp_paths:
        assert not temp_path.exists()


# Source: https://github.com/cookiecutter/cookiecutter-django/blob/f8897bfdff9681a28bc07b3361ab51bddb71a27c/tests/test_cookiecutter_generation.py
def test_project_generation(context, result):
    """Test that project is generated and fully rendered."""

    assert result.exit_code == 0
    assert result.exception is None
    assert result.project_path.name == context["__project_slug"]
    assert result.project_path.is_dir()

    check_temp_paths_are_removed(result)

    paths = build_files_list(result.project_path)
    assert paths
    check_paths(paths)


def test_project_generation_without_posix_credential_apis(
    cookies, context, monkeypatch, tmp_path
):
    """Render the project and run both hooks without credential POSIX APIs.

    Given injected missing O_NOFOLLOW and fchmod APIs in this process and
    hook subprocesses, Cookiecutter still renders every file and runs both
    hooks. Executing credential generation then fails with capability guidance.
    """
    unavailable = ("O_NOFOLLOW", "fchmod")
    marker = tmp_path / "hook-starts.txt"
    # Hook processes start fresh interpreters. Remove the APIs there as well as
    # in this process, and record that both hooks ran with the restriction.
    (tmp_path / "sitecustomize.py").write_text(
        "import os\n"
        f"for name in {unavailable!r}:\n"
        "    if hasattr(os, name):\n"
        "        delattr(os, name)\n"
        "with open(os.environ['HOOK_STARTS'], 'a') as stream:\n"
        "    stream.write('credential APIs unavailable\\n')\n"
    )
    monkeypatch.setenv("HOOK_STARTS", str(marker))
    pythonpath = [str(tmp_path), os.environ.get("PYTHONPATH", "")]
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(pythonpath))
    for name in unavailable:
        monkeypatch.delattr(os, name, raising=False)

    result = cookies.bake(extra_context={**context})

    assert result.exit_code == 0
    assert result.exception is None
    assert marker.read_text().splitlines() == ["credential APIs unavailable"] * 2
    assert not (result.project_path / "templates").exists()
    assert not (result.project_path / "secrets" / ".gitkeep").exists()
    assert not (result.project_path / "systemd" / ".gitkeep").exists()
    check_paths(build_files_list(result.project_path))

    monkeypatch.chdir(result.project_path)
    generator = runpy.run_path("scripts/generate_password_templates.py")
    with pytest.raises(RuntimeError, match="requires POSIX no-follow"):
        generator["render_template_files"](
            generator["JINJA_ENV"], generator["PASSWORD_FILES"], {}
        )
    assert not (result.project_path / ".env").exists()
