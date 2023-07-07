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

import os
import shutil
import tarfile
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "filepath",
    ["tmp_unit_test.tar.gz"],
)
@pytest.mark.parametrize(
    ("dirs", "toremove", "filenames"),
    [
        (
            [
                "tmp_unit_test/test/dir/for/unit/tests",
                "tmp_unit_test/test/dir/for/unit/things",
                "tmp_unit_test/files/dir",
            ],
            "tmp_unit_test",
            ["test_random.py", "test_utils.py", "test_xyz.py"],
        ),
    ],
)
@pytest.mark.parametrize(
    "tarball_read_mode",
    ["r:gz"],
)
def test_extract_tarfile(
    filepath, dirs, toremove, filenames, tarball_read_mode
) -> None:
    from dioptra_builtins.artifacts.utils import extract_tarfile

    # generate files for tarfile
    filelist = []
    for m in dirs:
        for q in filenames:
            path_to_file = Path(m) / q
            filelist += [path_to_file]
            if not os.path.exists(m):
                os.makedirs(Path(m))
            f = open(path_to_file, "w")
            f.write("random text")
            f.close()

    for p in filelist:
        assert os.path.exists(p)

    # create temporary tarfile
    tar_file = tarfile.open(filepath, "w:gz")
    for z in filelist:
        tar_file.add(z)
    tar_file.close()

    # delete directories
    for dd in dirs:
        for root, ds, files in os.walk(dd):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in ds:
                shutil.rmtree(os.path.join(root, d))

    # check successful deletion
    for p in filelist:
        print(p)
        assert not os.path.exists(p)

    # check tarfile exists
    assert os.path.exists(filepath)

    # extract tarfile
    extract_tarfile(filepath, tarball_read_mode)

    # check tarfile extraction
    for p in filelist:
        assert os.path.exists(p)

    # clean up tarfile
    os.remove(filepath)

    # clean up directories
    for z in toremove:
        if os.path.exists(z):
            shutil.rmtree(z)


@pytest.mark.parametrize(
    ("dirs", "toremove"),
    [
        (
            [
                "tmp_unit_test/test/dir/for/unit/tests",
                "tmp_unit_test/test/dir/for/unit/things",
                "tmp_unit_test/files/dir",
            ],
            ["tmp_unit_test"],
        ),
        ([], []),
        (["tmp_unit_test_srcs"], ["tmp_unit_test_srcs"]),
    ],
)
def test_make_directories(dirs, toremove) -> None:
    from dioptra_builtins.artifacts.utils import make_directories

    for z in toremove:
        if os.path.exists(z):
            shutil.rmtree(z)
    assert not any([os.path.exists(d) for d in dirs])
    make_directories(dirs)
    assert all([os.path.isdir(d) for d in dirs])
    for z in toremove:
        if os.path.exists(z):
            shutil.rmtree(z)
