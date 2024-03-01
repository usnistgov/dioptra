from pathlib import Path
from typing import Union


class UnsafeArchiveMemberPath(Exception):
    """
    Instances represent unsafe paths in an archive file.  E.g. those which
    contain "..", which might cause files to be written outside a target
    directory.
    """

    def __init__(self, archive_member_path: Union[str, Path]):
        message = "Unsafe archive member path: " + str(archive_member_path)
        super().__init__(message)

        self.archive_member_path = Path(archive_member_path)
