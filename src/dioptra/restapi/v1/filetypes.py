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
"""A File Type enumeration for handling the production of downloaded files."""
import enum
import io
import tarfile
import zipfile
from pathlib import Path
from typing import Callable, Iterable, Tuple, BinaryIO
from dioptra.restapi.db import models

_BundleEntry = Tuple[str, bytes]
Bundle = Iterable[_BundleEntry]


def _package_as_tarfile(entries: Bundle) -> BinaryIO:
    tar_fileobj = io.BytesIO()
    with tarfile.open(fileobj=tar_fileobj, mode="w:gz") as tar:
        for name, contents in entries:
            tf = tarfile.TarInfo(name)
            tf.size = len(contents)
            tar.addfile(tf, io.BytesIO(contents))
    tar_fileobj.seek(0)
    return tar_fileobj


def _package_as_zipfile(entries: Bundle) -> BinaryIO:
    zip_fileobj = io.BytesIO()
    with zipfile.ZipFile(zip_fileobj, mode="w") as zipf:
        for name, contents in entries:
            zipf.writestr(name, contents)

        # Mark the files as having been created on Windows so that
        # Unix permissions are not inferred as 0000
        for zf in zipf.filelist:
            zf.create_system = 0
    zip_fileobj.seek(0)
    return zip_fileobj


class FileTypes(enum.Enum):
    """
    Available FileTypes along with mimetype and suffix values
    """

    mimetype: str
    suffix: str
    package: Callable[[Bundle], BinaryIO]

    def __new__(
        cls,
        value: str,
        mimetype: str,
        suffix: str,
        package: Callable[[Bundle], BinaryIO],
    ):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.mimetype = mimetype
        obj.suffix = suffix
        obj.package = package
        return obj

    TAR_GZ = "tar_gz", "application/gzip", ".tar.gz", _package_as_tarfile
    ZIP = "zip", "application/zip", ".zip", _package_as_zipfile


def entrypoint_pluginfiles_to_bundle(
    plugin_files: list[models.EntryPointPluginFile],
) -> Bundle:
    def helper(entry: models.EntryPointPluginFile) -> _BundleEntry:
        plugin = entry.plugin
        plugin_file = entry.plugin_file

        path = Path(plugin.name) / plugin_file.filename
        contents = "" if plugin_file.contents is None else plugin_file.contents
        return (path.as_posix(), contents.encode("utf-8"))

    return map(helper, plugin_files)
