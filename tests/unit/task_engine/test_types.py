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
"""
Unit tests for the type classes.
"""
import pytest

from dioptra.sdk.exceptions.task_engine import InvalidTypeStructureDefinitionError
from dioptra.task_engine.type_registry import TYPE_INTEGER, TYPE_STRING
from dioptra.task_engine.types import (
    SimpleType,
    StructuredType,
    StructureType,
    TypeStructure,
    UnionType,
)


def test_simple_type() -> None:
    super_type = SimpleType("A")
    sub_type = SimpleType("B", super_type=super_type)

    assert super_type.name == "A"
    assert sub_type.name == "B"
    assert sub_type.super_type == super_type
    assert sub_type.is_subtype_of(super_type)
    assert not sub_type.is_subtype_of(sub_type)
    assert not super_type.is_subtype_of(sub_type)

    with pytest.raises(ValueError):
        SimpleType(None)


def test_simple_type_eq() -> None:
    type1 = SimpleType("B")
    type2 = SimpleType("B")

    assert type1 == type2
    assert hash(type1) == hash(type2)

    super_type = SimpleType("A")

    type1 = SimpleType("B", super_type=super_type)
    type2 = SimpleType("B", super_type=super_type)

    assert type1 == type2
    assert hash(type1) == hash(type2)


def test_simple_type_neq() -> None:
    type1 = SimpleType("A")
    type2 = SimpleType("B")

    assert type1 != type2
    # For the not-equal tests, hashes may be equal or not equal; there are
    # no requirements which we can subject to testing.


def test_list_structure() -> None:
    elt_type = SimpleType("A")

    list_struct = TypeStructure(StructureType.LIST, elt_type)

    assert list_struct.struct_type is StructureType.LIST
    assert list_struct.struct_def == elt_type

    with pytest.raises(InvalidTypeStructureDefinitionError):
        TypeStructure(StructureType.LIST, [elt_type])

    with pytest.raises(InvalidTypeStructureDefinitionError):
        TypeStructure(StructureType.LIST, {"foo": elt_type})


def test_list_structure_eq() -> None:
    elt_type = SimpleType("A")

    list_struct1 = TypeStructure(StructureType.LIST, elt_type)

    list_struct2 = TypeStructure(StructureType.LIST, elt_type)

    assert list_struct1 == list_struct2
    assert hash(list_struct1) == hash(list_struct2)


def test_list_structure_neq() -> None:
    elt_type1 = SimpleType("A")
    elt_type2 = SimpleType("B")

    list_struct1 = TypeStructure(StructureType.LIST, elt_type1)

    list_struct2 = TypeStructure(StructureType.LIST, elt_type2)

    assert list_struct1 != list_struct2


def test_tuple_structure() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")

    tuple_struct = TypeStructure(StructureType.TUPLE, [a_type, b_type])

    assert tuple_struct.struct_type is StructureType.TUPLE
    assert tuple_struct.struct_def == [a_type, b_type]

    with pytest.raises(InvalidTypeStructureDefinitionError):
        TypeStructure(StructureType.TUPLE, a_type)

    with pytest.raises(InvalidTypeStructureDefinitionError):
        TypeStructure(StructureType.TUPLE, {"foo": a_type})

    # Allowed corner case: empty tuple structure
    TypeStructure(StructureType.TUPLE, [])


def test_tuple_structure_eq() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")

    tuple_struct1 = TypeStructure(StructureType.TUPLE, [a_type, b_type])

    tuple_struct2 = TypeStructure(StructureType.TUPLE, [a_type, b_type])

    assert tuple_struct1 == tuple_struct2
    assert hash(tuple_struct1) == hash(tuple_struct2)


def test_tuple_structure_neq() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")
    c_type = SimpleType("C")

    tuple_struct1 = TypeStructure(StructureType.TUPLE, [a_type, b_type])

    tuple_struct2 = TypeStructure(StructureType.TUPLE, [b_type, a_type])

    tuple_struct3 = TypeStructure(StructureType.TUPLE, [b_type, c_type])

    assert tuple_struct1 != tuple_struct2
    assert tuple_struct2 != tuple_struct3


def test_mapping_structure_enum() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")

    map_struct = TypeStructure(StructureType.MAPPING, {"foo": a_type, "bar": b_type})

    assert map_struct.struct_type is StructureType.MAPPING
    assert map_struct.struct_def == {"foo": a_type, "bar": b_type}

    with pytest.raises(InvalidTypeStructureDefinitionError):
        TypeStructure(StructureType.MAPPING, a_type)

    # Allowed corner case: empty enumerated mapping structure
    TypeStructure(StructureType.MAPPING, {})


def test_mapping_structure_enum_eq() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")

    map_struct1 = TypeStructure(
        StructureType.MAPPING,
        dict(
            [
                # This construction allows us to force particular dict iteration
                # orders.
                ("foo", a_type),
                ("bar", b_type),
            ]
        ),
    )

    map_struct2 = TypeStructure(
        StructureType.MAPPING, dict([("bar", b_type), ("foo", a_type)])
    )

    assert map_struct1 == map_struct2
    assert hash(map_struct1) == hash(map_struct2)


def test_mapping_structure_enum_neq() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")
    c_type = SimpleType("C")

    map_struct1 = TypeStructure(StructureType.MAPPING, {"foo": a_type, "bar": b_type})

    map_struct2 = TypeStructure(StructureType.MAPPING, {"bar": b_type, "foo": c_type})

    map_struct3 = TypeStructure(StructureType.MAPPING, {"baz": a_type, "bar": b_type})

    assert map_struct1 != map_struct2
    assert map_struct1 != map_struct3


def test_mapping_structure_key_value_type() -> None:
    a_type = SimpleType("A")

    map_struct = TypeStructure(StructureType.MAPPING, [TYPE_STRING, a_type])

    assert map_struct.struct_type is StructureType.MAPPING
    assert map_struct.struct_def == [TYPE_STRING, a_type]


def test_mapping_structure_key_value_eq() -> None:
    a_type = SimpleType("A")

    map_struct1 = TypeStructure(StructureType.MAPPING, [TYPE_STRING, a_type])

    map_struct2 = TypeStructure(StructureType.MAPPING, [TYPE_STRING, a_type])

    assert map_struct1 == map_struct2
    assert hash(map_struct1) == hash(map_struct2)


def test_mapping_structure_key_value_neq() -> None:
    a_type = SimpleType("A")

    map_struct1 = TypeStructure(StructureType.MAPPING, [TYPE_STRING, a_type])

    map_struct2 = TypeStructure(StructureType.MAPPING, [TYPE_STRING, TYPE_INTEGER])

    map_struct3 = TypeStructure(StructureType.MAPPING, [TYPE_INTEGER, a_type])

    assert map_struct1 != map_struct2
    assert map_struct1 != map_struct3
    assert map_struct2 != map_struct3


def test_structured_type_list() -> None:
    elt_type = SimpleType("A")
    list_structure = TypeStructure(StructureType.LIST, elt_type)
    list_type = StructuredType(list_structure, name="list_of_A")

    assert list_type.name == "list_of_A"
    assert list_type.structure == list_structure

    list_type_anon = StructuredType(list_structure)

    assert not list_type_anon.name
    assert list_type_anon.structure == list_structure


def test_structured_type_list_eq() -> None:
    elt_type = SimpleType("A")
    list_structure = TypeStructure(StructureType.LIST, elt_type)
    list_type1 = StructuredType(list_structure, name="list_of_A")
    list_type2 = StructuredType(list_structure, name="list_of_A")
    list_type_anon1 = StructuredType(list_structure)
    list_type_anon2 = StructuredType(list_structure)

    assert list_type1 == list_type2
    assert hash(list_type1) == hash(list_type2)

    assert list_type_anon1 == list_type_anon2
    assert hash(list_type_anon1) == hash(list_type_anon2)


def test_structured_type_list_neq() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")
    list_structure1 = TypeStructure(StructureType.LIST, a_type)
    list_structure2 = TypeStructure(StructureType.LIST, b_type)
    list_type1 = StructuredType(list_structure1, name="list_of_A")
    list_type2 = StructuredType(list_structure2, name="list_of_B")
    list_type_anon1 = StructuredType(list_structure1)
    list_type_anon2 = StructuredType(list_structure2)

    assert list_type1 != list_type2
    assert list_type1 != list_type_anon1
    assert list_type_anon1 != list_type_anon2


def test_structured_type_tuple() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")
    tuple_structure = TypeStructure(StructureType.TUPLE, [a_type, b_type])
    tuple_type = StructuredType(tuple_structure, name="tuple_A_B")
    tuple_type_anon = StructuredType(tuple_structure)

    assert tuple_type.name == "tuple_A_B"
    assert tuple_type.structure == tuple_structure

    assert not tuple_type_anon.name
    assert tuple_type_anon.structure == tuple_structure

    # Allowed corner case: empty tuple type
    StructuredType(TypeStructure(StructureType.TUPLE, []), name="empty_tuple")


def test_structured_type_tuple_eq() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")
    tuple_structure = TypeStructure(StructureType.TUPLE, [a_type, b_type])
    tuple_type1 = StructuredType(tuple_structure, name="tuple_A_B")
    tuple_type2 = StructuredType(tuple_structure, name="tuple_A_B")
    tuple_type_anon1 = StructuredType(tuple_structure)
    tuple_type_anon2 = StructuredType(tuple_structure)

    assert tuple_type1 == tuple_type2
    assert hash(tuple_type1) == hash(tuple_type2)

    assert tuple_type_anon1 == tuple_type_anon2
    assert hash(tuple_type_anon1) == hash(tuple_type_anon2)


def test_structured_type_tuple_neq() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")
    c_type = SimpleType("C")
    tuple_structure1 = TypeStructure(StructureType.TUPLE, [a_type, b_type])
    tuple_structure2 = TypeStructure(StructureType.TUPLE, [b_type, a_type])
    tuple_structure3 = TypeStructure(StructureType.TUPLE, [b_type, c_type])
    tuple_type1 = StructuredType(tuple_structure1, name="tuple_A_B")
    tuple_type2 = StructuredType(tuple_structure2, name="tuple_B_A")
    tuple_type3 = StructuredType(tuple_structure3, name="tuple_B_C")
    tuple_type_anon1 = StructuredType(tuple_structure1)
    tuple_type_anon2 = StructuredType(tuple_structure2)
    tuple_type_anon3 = StructuredType(tuple_structure2)

    assert tuple_type1 != tuple_type2
    assert tuple_type1 != tuple_type3
    assert tuple_type1 != tuple_type_anon1
    assert tuple_type1 != tuple_type_anon2
    assert tuple_type1 != tuple_type_anon3
    assert tuple_type_anon1 != tuple_type_anon2
    assert tuple_type_anon1 != tuple_type_anon3


def test_structured_type_mapping_enum() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")
    map_structure = TypeStructure(StructureType.MAPPING, {"foo": a_type, "bar": b_type})
    map_type = StructuredType(map_structure, name="map_foo_bar")
    map_type_anon = StructuredType(map_structure)

    assert map_type.name == "map_foo_bar"
    assert map_type.structure == map_structure
    assert not map_type_anon.name
    assert map_type_anon.structure == map_structure

    # Allowed corner case: empty enumerated mapping type
    StructuredType(TypeStructure(StructureType.MAPPING, {}), name="empty_enum_mapping")


def test_structured_type_mapping_enum_eq() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")
    map_structure1 = TypeStructure(
        StructureType.MAPPING, dict([("foo", a_type), ("bar", b_type)])
    )
    map_structure2 = TypeStructure(
        StructureType.MAPPING, dict([("bar", b_type), ("foo", a_type)])
    )
    map_type1 = StructuredType(map_structure1, name="map_foo_bar")
    map_type2 = StructuredType(map_structure2, name="map_foo_bar")
    map_type_anon1 = StructuredType(map_structure1)
    map_type_anon2 = StructuredType(map_structure2)

    assert map_type1 == map_type2
    assert hash(map_type1) == hash(map_type2)

    assert map_type_anon1 == map_type_anon2
    assert hash(map_type_anon1) == hash(map_type_anon2)


def test_structured_type_mapping_enum_neq() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")
    c_type = SimpleType("C")
    map_structure1 = TypeStructure(
        StructureType.MAPPING, dict([("foo", a_type), ("bar", b_type)])
    )
    map_structure2 = TypeStructure(
        StructureType.MAPPING, dict([("bar", c_type), ("foo", a_type)])
    )
    map_structure3 = TypeStructure(
        StructureType.MAPPING, dict([("foo", a_type), ("baz", b_type)])
    )
    map_type1 = StructuredType(map_structure1, name="map_foo_bar")
    map_type2 = StructuredType(map_structure2, name="map_bar_foo")
    map_type3 = StructuredType(map_structure3, name="map_foo_baz")
    map_type_anon1 = StructuredType(map_structure1)
    map_type_anon2 = StructuredType(map_structure2)
    map_type_anon3 = StructuredType(map_structure3)

    assert map_type1 != map_type2
    assert map_type1 != map_type3
    assert map_type1 != map_type_anon1
    assert map_type1 != map_type_anon2
    assert map_type1 != map_type_anon3
    assert map_type_anon1 != map_type_anon2
    assert map_type_anon1 != map_type_anon3


def test_structured_type_mapping_key_value() -> None:
    a_type = SimpleType("A")
    map_structure = TypeStructure(StructureType.MAPPING, [TYPE_STRING, a_type])
    map_type = StructuredType(map_structure, name="map_string_a")
    map_type_anon = StructuredType(map_structure)

    assert map_type.name == "map_string_a"
    assert map_type.structure == map_structure

    assert not map_type_anon.name
    assert map_type_anon.structure == map_structure


def test_structured_type_mapping_key_value_eq() -> None:
    a_type = SimpleType("A")
    map_structure = TypeStructure(StructureType.MAPPING, [TYPE_STRING, a_type])
    map_type1 = StructuredType(map_structure, name="map_string_a")
    map_type2 = StructuredType(map_structure, name="map_string_a")
    map_type_anon1 = StructuredType(map_structure)
    map_type_anon2 = StructuredType(map_structure)

    assert map_type1 == map_type2
    assert hash(map_type1) == hash(map_type2)

    assert map_type_anon1 == map_type_anon2
    assert hash(map_type_anon1) == hash(map_type_anon2)


def test_structured_type_mapping_key_value_neq() -> None:
    a_type = SimpleType("A")
    map_structure1 = TypeStructure(StructureType.MAPPING, [TYPE_STRING, a_type])
    map_structure2 = TypeStructure(StructureType.MAPPING, [TYPE_STRING, TYPE_INTEGER])
    map_structure3 = TypeStructure(StructureType.MAPPING, [TYPE_INTEGER, a_type])
    map_type1 = StructuredType(map_structure1, name="map_string_a")
    map_type2 = StructuredType(map_structure2, name="map_string_int")
    map_type3 = StructuredType(map_structure3, name="map_int_a")
    map_type_anon1 = StructuredType(map_structure1)
    map_type_anon2 = StructuredType(map_structure2)
    map_type_anon3 = StructuredType(map_structure3)

    assert map_type1 != map_type2
    assert map_type1 != map_type3
    assert map_type1 != map_type_anon1
    assert map_type1 != map_type_anon2
    assert map_type1 != map_type_anon3
    assert map_type2 != map_type3
    assert map_type_anon1 != map_type_anon2
    assert map_type_anon1 != map_type_anon3
    assert map_type_anon2 != map_type_anon3


def test_structured_type_no_structure() -> None:
    with pytest.raises(ValueError):
        StructuredType(None)


def test_union_type() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")

    union_type = UnionType([a_type, b_type], name="union_a_b")

    assert union_type.name == "union_a_b"
    assert union_type.member_types == {b_type, a_type}

    union_type_anon = UnionType([a_type, b_type])

    assert not union_type_anon.name
    assert union_type_anon.member_types == {b_type, a_type}

    # Allowed corner case: empty union
    UnionType([], name="empty_union")


def test_union_type_eq() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")

    union_type1 = UnionType([a_type, b_type], name="union_a_b")
    union_type2 = UnionType([b_type, a_type], name="union_a_b")
    union_type_anon1 = UnionType([a_type, b_type])
    union_type_anon2 = UnionType([b_type, a_type])

    assert union_type1 == union_type2
    assert hash(union_type1) == hash(union_type2)

    assert union_type_anon1 == union_type_anon2
    assert hash(union_type_anon1) == hash(union_type_anon2)


def test_union_type_neq() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")
    c_type = SimpleType("C")

    union_type1 = UnionType([a_type, b_type], name="union_a_b")
    union_type2 = UnionType([a_type, c_type], name="union_a_c")
    union_type_anon1 = UnionType([a_type, b_type])
    union_type_anon2 = UnionType([a_type, c_type])

    assert union_type1 != union_type2
    assert union_type1 != union_type_anon1
    assert union_type1 != union_type_anon2
    assert union_type_anon1 != union_type_anon2
