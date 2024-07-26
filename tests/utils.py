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

import io
import tarfile
import timeit
from pathlib import Path
from typing import List, Mapping, Optional, Union

PathLike = List[Union[str, Path]]


class Timer(object):
    def __init__(self, timeout: Optional[float] = None) -> None:
        self.start = timeit.default_timer()
        self._elapsed: Optional[float] = None
        self._timeout = timeout

    def __enter__(self) -> Timer:
        self.start = timeit.default_timer()
        self._elapsed = None
        return self

    def __exit__(self, *args) -> None:
        self._elapsed = timeit.default_timer() - self.start

    @property
    def elapsed(self) -> float:
        if self._elapsed is not None:
            return self._elapsed

        return timeit.default_timer() - self.start

    @property
    def timeout_exceeded(self) -> bool:
        if self._timeout is None:
            return False

        return self._timeout < self.elapsed


def make_tarball_bytes(tar_content: Mapping[str, bytes]) -> bytes:
    """
    Make a tarball containing the given content.  Return the tarball content
    as bytes.

    Args:
        tar_content: A mapping from file path to bytes, which lays out the
            paths and file content which should go into the tarball.

    Returns:
        Tarball bytes
    """

    tar_content_stream = io.BytesIO()
    tf = tarfile.TarFile.open(fileobj=tar_content_stream, mode="w:gz")

    for filepath, file_content in tar_content.items():
        ti = tarfile.TarInfo(filepath)
        ti.size = len(file_content)

        tf.addfile(ti, io.BytesIO(file_content))

    tf.close()

    return tar_content_stream.getvalue()
