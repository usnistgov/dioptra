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
import io
from collections.abc import Iterable, Mapping
from typing import Any

import sqlalchemy as sa
import sqlalchemy.orm as sao


def depth_limited_repr(value: Any, max_depth: int = 2) -> str:
    """
    Create a repr string for the given instance, with a depth limit to avoid
    excessively large reprs.  Where the repr would exceed the depth cutoff,
    it includes "..." as a placeholder.

    The depth does not count depth of normal list/map-like data structures; it
    counts nested instances of ORM-mapped objects.  If a data structure is
    passed which does not contain any ORM instances, max_depth will have no
    effect and the value will be repr'd in its entirety.

    Args:
        value: The value to repr
        max_depth: A maximum depth

    Returns:
        A repr string
    """
    buf = io.StringIO()
    _depth_limited_repr(value, buf, max_depth)

    return buf.getvalue()


def _depth_limited_repr(value: Any, out: io.TextIOBase, max_depth: int) -> None:
    """
    Write a repr of the given value to the given stream.

    Args:
        value: The value to repr
        out: A textual output stream
        max_depth: A maximum depth
    """
    if isinstance(value, sao.DeclarativeBase):
        # Let depth be only applicable here; the primary use case for this
        # function is to limit traversal of ORM object graphs, not arbitrary
        # data structures.
        if max_depth <= 0:
            out.write("...")

        else:
            _depth_limited_orm_object_repr(value, out, max_depth - 1)

    elif isinstance(value, Mapping):
        _depth_limited_map_repr(value, out, max_depth)

    # Pretty general; will include tuples and sets too.  Do we care about
    # having a more "faithful" repr for them?
    elif isinstance(value, Iterable) and not isinstance(value, (str, bytes, bytearray)):
        _depth_limited_iter_repr(value, out, max_depth)

    else:
        out.write(repr(value))


def _depth_limited_orm_object_repr(
    obj: sao.DeclarativeBase, out: io.TextIOBase, max_depth: int
) -> None:
    """
    Write a repr of the given ORM-mapped object to the given stream.

    Args:
        obj: The ORM-mapped object
        out: A textual output stream
        max_depth: A maximum depth
    """
    state = sa.inspect(obj)
    if state is None:
        # Is it possible to have an instance of an ORM-mapped class,
        # which SQLAlchemy does not know about?
        out.write("<unknown>")

    else:
        out.write(type(obj).__name__)
        out.write("(")
        first = True
        for attr_name, attr_state in state.attrs.items():
            if not first:
                out.write(", ")
            first = False

            out.write(attr_name)
            out.write("=")
            _depth_limited_repr(attr_state.value, out, max_depth)

        out.write(")")


def _depth_limited_iter_repr(
    it: Iterable[Any], out: io.TextIOBase, max_depth: int
) -> None:
    """
    Write a repr of the given iterable value to the given stream.  This
    function will build a bracketed list-like syntax.

    Args:
        it: an Iterable
        out: A textual output stream
        max_depth: A maximum depth
    """
    out.write("[")
    first = True
    for value in it:
        if not first:
            out.write(", ")
        first = False

        _depth_limited_repr(value, out, max_depth)

    out.write("]")


def _depth_limited_map_repr(mapp: Mapping, out: io.TextIOBase, max_depth: int) -> None:
    """
    Write a repr of the given mapping value to the given stream.  This function
    will build a JSON-like syntax with braces and key/value pairs.

    Args:
        mapp: A mapping
        out: A textual output stream
        max_depth: A maximum depth
    """

    out.write("{")
    first = True
    for k, v in mapp.items():
        if not first:
            out.write(", ")
        first = False

        out.write(repr(k))
        out.write(": ")
        _depth_limited_repr(v, out, max_depth)

    out.write("}")
