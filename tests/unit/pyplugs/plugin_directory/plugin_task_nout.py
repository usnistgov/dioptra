# NOTICE
#
# This software (or technical data) was produced for the U. S. Government under
# contract SB-1341-14-CQ-0010, and is subject to the Rights in Data-General Clause
# 52.227-14, Alt. IV (DEC 2007)
#
# © 2021 The MITRE Corporation.
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
