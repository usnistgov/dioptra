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
import pytest
from dioptra.restapi.db.models.utils import depth_limited_repr
import sqlalchemy as sa
import sqlalchemy.orm as sao


class TestBase(sao.DeclarativeBase):
    pass


class A(TestBase):
    __tablename__ = "A"
    id: sao.Mapped[int] = sao.mapped_column(primary_key=True)
    bs: sao.Mapped[list["B"]] = sao.relationship()


class B(TestBase):
    __tablename__ = "B"
    id: sao.Mapped[int] = sao.mapped_column(primary_key=True)
    a_id: sao.Mapped[int] = sao.mapped_column(sa.ForeignKey("A.id"))
    cs: sao.Mapped[list["C"]] = sao.relationship()


class C(TestBase):
    __tablename__ = "C"
    id: sao.Mapped[int] = sao.mapped_column(primary_key=True)
    b_id: sao.Mapped[int] = sao.mapped_column(sa.ForeignKey("B.id"))


@pytest.mark.parametrize(
    "struct, expected_repr", [
        (1, "1"),
        ("a", "'a'"),
        (False, "False"),
        (None, "None"),
        (b"abc", "b'abc'"),
        (bytearray(b'abc'), "bytearray(b'abc')"),
        ([], "[]"),
        ([1], "[1]"),
        ([1, "foo"], "[1, 'foo']"),
        ([[[1]]], "[[[1]]]"),
        ({}, "{}"),
        ({1: "a"}, "{1: 'a'}"),
        ({"a": 1}, "{'a': 1}"),
        ({"a": 1, 2: "b"}, "{'a': 1, 2: 'b'}"),
        (range(3), "[0, 1, 2]"),
        ({1, 2, 3}, "[1, 2, 3]"),
        ((1, 2, 3), "[1, 2, 3]"),
    ]
)
def test_simple_repr(struct, expected_repr):

    # max depth limit should not matter for these
    dr = depth_limited_repr(struct, 0)
    assert dr == expected_repr

    dr = depth_limited_repr(struct, 999)
    assert dr == expected_repr


def test_orm_repr_nest_0():

    a = A(id=1)

    dr = depth_limited_repr(a, 0)
    assert dr == "..."

    dr = depth_limited_repr(a, 1)
    # I dunno if attributes will have any reliable ordering in reprs
    assert dr == "A(bs=[], id=1)"


def test_orm_repr_nest_1():

    b = B(id=2)
    a = A(id=1, bs=[b])

    dr = depth_limited_repr(a, 0)
    assert dr == "..."

    dr = depth_limited_repr(a, 1)
    assert dr == "A(bs=[...], id=1)"

    dr = depth_limited_repr(a, 2)
    # a_id==None: remember foreign key attributes are not automatically set...
    assert dr == "A(bs=[B(cs=[], id=2, a_id=None)], id=1)"


def test_orm_repr_nest_2():

    c = C(id=3)
    b = B(id=2, cs=[c])
    a = A(id=1, bs=[b])

    dr = depth_limited_repr(a, 0)
    assert dr == "..."

    dr = depth_limited_repr(a, 1)
    assert dr == "A(bs=[...], id=1)"

    dr = depth_limited_repr(a, 2)
    assert dr == "A(bs=[B(cs=[...], id=2, a_id=None)], id=1)"

    dr = depth_limited_repr(a, 3)
    assert dr == "A(bs=[B(cs=[C(id=3, b_id=None)], id=2, a_id=None)], id=1)"


def test_orm_mixed():

    b = B(id=2)
    a = A(id=1, bs=[b])

    value = {
        "a": {
            "b": [
                1,
                a
            ]
        }
    }

    # depth does not affect traversal of plain data structures, only the
    # ORM instances
    dr = depth_limited_repr(value, 0)
    assert dr == "{'a': {'b': [1, ...]}}"

    dr = depth_limited_repr(value, 1)
    assert dr == "{'a': {'b': [1, A(bs=[...], id=1)]}}"

    dr = depth_limited_repr(value, 2)
    assert dr == "{'a': {'b': [1, A(bs=[B(cs=[], id=2, a_id=None)], id=1)]}}"
