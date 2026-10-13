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
import tarfile
from io import BytesIO
from pathlib import Path
from typing import Optional, Union

import pytest
import structlog
from structlog.stdlib import BoundLogger

from dioptra.restapi.v1.shared import io_file_service as file_io
from dioptra.restapi.v1.shared.io_file_service import IOFileService

LOGGER: BoundLogger = structlog.stdlib.get_logger()


@pytest.mark.parametrize(
    ("mode", "preserve_paths", "strip_root", "expected"),
    [
        ("w:gz", False, False, "file.py"),
        ("w:", True, False, "snapshot/nested/file.py"),
        ("w:gz", True, True, "nested/file.py"),
    ],
)
def test_safe_extract_archive(
    io_file_service, tmp_path, mode, preserve_paths, strip_root, expected
):
    with _archive(
        [
            ("snapshot/", tarfile.DIRTYPE, b""),
            ("snapshot/nested/file.py", tarfile.REGTYPE, b"contents"),
        ],
        mode,
    ) as archive:
        extracted = io_file_service.safe_extract_archive(
            tmp_path,
            archive_fileobj=archive,
            preserve_paths=preserve_paths,
            strip_root=strip_root,
        )
    assert extracted == [str(tmp_path / expected)]
    assert (tmp_path / expected).read_bytes() == b"contents"


def test_sanitize_file_path(io_file_service: IOFileService) -> None:
    clean_file_path1 = io_file_service.sanitize_file_path(
        filepath="dir/subdir/testfile.txt", path_prefix="/tmp"
    )
    clean_file_path2 = io_file_service.sanitize_file_path(
        filepath="dir/subdir/testfile.txt"
    )
    clean_file_path3 = io_file_service.sanitize_file_path(
        filepath="../testfile.txt", path_prefix="/tmp"
    )

    assert clean_file_path1 == Path("/tmp") / "testfile.txt"
    assert clean_file_path2 == Path.cwd() / "testfile.txt"
    assert clean_file_path3 == Path("/tmp") / "testfile.txt"


@pytest.mark.parametrize(
    "path, expected_result",
    [
        # assume fixed "/pre" prefix
        ("/foo/bar", None),
        ("foo/bar", "/pre/foo/bar"),
        ("/foo/../bar", None),
        ("foo/../bar", None),
    ],
)
def test_sanitize_file_path_preserve(
    io_file_service: IOFileService,
    path: str,
    expected_result: Optional[Union[str, Path]],
) -> None:
    actual_result = io_file_service.sanitize_file_path(path, "/pre", True)

    # wrap expected_result in a Path object, to make the below comparison work
    if expected_result is not None:
        expected_result = Path(expected_result)

    assert actual_result == expected_result


@pytest.mark.skipif(os.name != "nt", reason="requires Windows")
@pytest.mark.parametrize(
    "path, expected_result",
    [
        # assume fixed "/pre" prefix
        (r"C:\foo\bar", None),
        (r"C:foo\bar", None),
        (r"C:\foo\..\bar", None),
        (r"C:foo\..\bar", None),
    ],
)
def test_sanitize_file_path_preserve_windows(
    io_file_service: IOFileService,
    path: str,
    expected_result: Optional[Union[str, Path]],
) -> None:
    actual_result = io_file_service.sanitize_file_path(path, "/pre", True)

    # wrap expected_result in a Path object, to make the below comparison work
    if expected_result is not None:
        expected_result = Path(expected_result)

    assert actual_result == expected_result


@pytest.mark.parametrize(
    ("name", "strip_root"),
    [("/outside", False), ("../outside", False), ("../outside", True)],
)
def test_unsafe_tarball_path(name, strip_root, tmp_path, io_file_service):
    # Validate before stripping the wrapper: '../outside' must not become 'outside'.
    with _archive([(name, tarfile.REGTYPE, b"")]) as archive:
        with pytest.raises(ValueError, match="safe relative path"):
            io_file_service.safe_extract_archive(
                tmp_path,
                archive_fileobj=archive,
                preserve_paths=True,
                strip_root=strip_root,
            )


def _archive(entries, mode="w:gz"):
    """Build a tar stream from explicit (name, type, contents) entries."""
    output = BytesIO()
    with tarfile.open(fileobj=output, mode=mode) as tar:
        for name, type_, contents in entries:
            member = tarfile.TarInfo(name)
            member.type = type_
            member.size = len(contents)
            member.linkname = "/outside"
            tar.addfile(member, BytesIO(contents))
    output.seek(0)
    return output


@pytest.mark.parametrize("name", ["../outside", "/outside"])
def test_write_file_rejects_unsafe_path(name, tmp_path, io_file_service):
    destination = tmp_path / "extracted"
    with pytest.raises(ValueError, match="safe relative path"):
        io_file_service.write_file(destination, name, BytesIO(b"contents"))
    assert not destination.exists()


@pytest.mark.parametrize("type_", [tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.CHRTYPE])
def test_archive_rejects_links_and_special_files(type_, tmp_path, io_file_service):
    destination = tmp_path / "extracted"
    with _archive([("snapshot/entry", type_, b"")]) as archive:
        with pytest.raises(ValueError, match="unsafe entry"):
            io_file_service.safe_extract_archive(
                destination,
                archive_fileobj=archive,
                preserve_paths=True,
            )
    assert not destination.exists()


@pytest.mark.parametrize(
    "paths", [("parent", "parent/file"), ("parent/file", "parent")]
)
def test_write_file_rejects_file_directory_conflicts(paths, tmp_path, io_file_service):
    io_file_service.write_file(tmp_path, paths[0], BytesIO(b"original"))
    with pytest.raises(ValueError, match="conflict"):
        io_file_service.write_file(tmp_path, paths[1], BytesIO(b"replacement"))
    assert (tmp_path / paths[0]).read_bytes() == b"original"


def test_write_file_rejects_preexisting_symlink(tmp_path, io_file_service):
    root = tmp_path / "import"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "link").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        io_file_service.write_file(root, "link/file", BytesIO(b"contents"))
    assert list(outside.iterdir()) == []


def test_write_file_limits_actual_stream_content(
    monkeypatch, tmp_path, io_file_service
):
    monkeypatch.setattr(file_io, "MAX_FILE_BYTES", 4)
    monkeypatch.setattr(file_io, "CHUNK_SIZE", 2)
    with pytest.raises(ValueError, match="file exceeds"):
        io_file_service.write_file(tmp_path, "file", BytesIO(b"12345"))
    assert (tmp_path / "file").read_bytes() == b"1234"


def test_archive_duplicate_entries_do_not_overwrite(tmp_path, io_file_service):
    with _archive(
        [
            ("snapshot/file", tarfile.REGTYPE, b"original"),
            ("snapshot/file", tarfile.REGTYPE, b"replacement"),
        ]
    ) as archive:
        with pytest.raises(ValueError, match="duplicate"):
            io_file_service.safe_extract_archive(
                tmp_path,
                archive_fileobj=archive,
                preserve_paths=True,
            )
    assert (tmp_path / "snapshot/file").read_bytes() == b"original"


def test_provider_archive_rejects_multiple_roots(tmp_path, io_file_service):
    with _archive(
        [
            ("snapshot/file", tarfile.REGTYPE, b""),
            ("other/file", tarfile.REGTYPE, b""),
        ]
    ) as archive:
        with pytest.raises(ValueError, match="one wrapper directory"):
            io_file_service.safe_extract_archive(
                tmp_path, archive_fileobj=archive, preserve_paths=True, strip_root=True
            )


@pytest.mark.parametrize(
    ("setting", "limit", "message"),
    [
        ("MAX_FILE_BYTES", 2, "file exceeds"),
        ("MAX_TOTAL_BYTES", 5, "total content"),
        ("MAX_ENTRIES", 1, "too many entries"),
    ],
)
def test_archive_content_and_entry_limits(
    setting, limit, message, monkeypatch, tmp_path, io_file_service
):
    monkeypatch.setattr(file_io, setting, limit)
    with _archive(
        [
            ("snapshot/first", tarfile.REGTYPE, b"123"),
            ("snapshot/second", tarfile.REGTYPE, b"456"),
        ]
    ) as archive:
        with pytest.raises(ValueError, match=message):
            io_file_service.safe_extract_archive(
                tmp_path,
                archive_fileobj=archive,
                preserve_paths=True,
            )


def test_resource_read_rejects_symlink_escape(tmp_path, io_file_service):
    root = tmp_path / "import"
    root.mkdir()
    (root / "link").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="escapes the import directory"):
        io_file_service.resolve_import_path(root, "link/outside")
