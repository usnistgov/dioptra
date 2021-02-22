"""Exceptions for the metrics plugins collection"""

from mitre.securingai.sdk.exceptions.base import BaseTaskPluginError


class UnknownDistanceMetricError(BaseTaskPluginError):
    """The requested distance metric could not be located"""


class UnknownPerformanceMetricError(BaseTaskPluginError):
    """The requested performance metric could not be located"""
