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
#
# This is a fork of the work
# https://github.com/gahjelle/pyplugs/blob/c75a5e1693691adc22bf91d01fad63aa67189d73/pyplugs/__init__.py  # noqa: B950
# See copyright below.
#
# Copyright (c) 2019 Geir Arne Hjelle
# Distributed under the terms of the MIT License.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""PyPlugs, decorator based plug-in architecture for Python

See {url} for more information.

Current maintainers:
--------------------

{maintainers}
"""
from __future__ import annotations

# Standard library imports
from collections import namedtuple as _namedtuple
from datetime import date as _date

from ._plugins import *  # noqa

__url__ = "https://pages.nist.gov/dioptra"


# Authors/maintainers of Pyplugs
_Author = _namedtuple("_Author", ["name", "email", "start", "end"])
_AUTHORS = [
    _Author(
        "James Glasbrenner", "jglasbrenner@mitre.org", _date(2020, 11, 24), _date.max
    ),
    _Author("Cory Miniter", "jminiter@mitre.org", _date(2020, 11, 24), _date.max),
    _Author("Howard Huang", "hhuang@mitre.org", _date(2020, 11, 24), _date.max),
    _Author("Julian Sexton", "jtsexton@mitre.org", _date(2020, 11, 24), _date.max),
    _Author("Paul Rowe", "prowe@mitre.org", _date(2020, 11, 24), _date.max),
    _Author(
        "Geir Arne Hjelle", "geirarne@gmail.com", _date(2019, 4, 1), _date(2020, 11, 23)
    ),
]

__author__ = ", ".join(a.name for a in _AUTHORS if a.start <= _date.today() < a.end)
__contact__ = ", ".join(a.email for a in _AUTHORS if a.start <= _date.today() < a.end)


# Update doc with info about maintainers
def _update_doc(doc: str) -> str:
    """Add information to doc-string

    Args:
        doc:  The doc-string to update.

    Returns:
        The updated doc-string.
    """
    # Maintainers
    maintainer_list = [
        f"+ {a.name} <{a.email}>" for a in _AUTHORS if a.start <= _date.today() < a.end
    ]
    maintainers = "\n".join(maintainer_list)

    # Add to doc-string
    return doc.format(maintainers=maintainers, url=__url__)


__doc__ = _update_doc(__doc__)
