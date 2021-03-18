"""A task plugin module of exceptions for the artifacts plugins collection."""

from mitre.securingai.sdk.exceptions.base import BaseTaskPluginError


class UnsupportedDataFrameFileFormatError(BaseTaskPluginError):
    """The requested data frame file format is not supported."""
