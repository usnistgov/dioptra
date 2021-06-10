# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
"""A task plugin module of exceptions for the artifacts plugins collection."""

from mitre.securingai.sdk.exceptions.base import BaseTaskPluginError


class UnsupportedDataFrameFileFormatError(BaseTaskPluginError):
    """The requested data frame file format is not supported."""
