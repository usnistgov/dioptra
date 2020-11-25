# This is a fork of the work
# https://github.com/gahjelle/pyplugs/blob/c75a5e1693691adc22bf91d01fad63aa67189d73/pyplugs/__init__.py
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

# Standard library imports
from collections import namedtuple as _namedtuple
from datetime import date as _date

from ._exceptions import *  # noqa
from ._plugins import *  # noqa

__version__ = "0.0.0"


__url__ = "https://secure-ai.pages.mitre.org/securing-ai-lab-components"


# Authors/maintainers of Pyplugs
_Author = _namedtuple("_Author", ["name", "email", "start", "end"])
_AUTHORS = [
    _Author(
        "James Glasbrenner", "jglasbrenner@mitre.org", _date(2020, 11, 24), _date.max
    ),
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
