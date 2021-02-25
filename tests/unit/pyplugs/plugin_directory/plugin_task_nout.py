"""Example of a plug-in consisting of several parts"""
from mitre.securingai import pyplugs


@pyplugs.register
@pyplugs.task_nout(2)
def plugin_with_nout():
    """A plugin returning a tuple marked with nout for compatibility with prefect."""
    return "output1", "output2"


@pyplugs.register
def plugin_without_nout():
    """A plugin returning a tuple."""
    return "output1", "output2"
