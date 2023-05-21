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
Test building types from type definitions.
"""
from collections.abc import Mapping
from typing import Any

import pytest

from dioptra.sdk.exceptions.task_engine import (
    AnonymousSimpleTypeError,
    BuiltinTypeRedefinitionError,
    DioptraTypeError,
    InvalidKeyTypeError,
    NonSimpleSuperTypeError,
    TooManyTypeStructuresError,
    TypeNotFoundError,
    TypeReferenceCycleError,
)
from dioptra.task_engine.type_registry import (
    TYPE_ANY,
    TYPE_BOOLEAN,
    TYPE_INTEGER,
    TYPE_NULL,
    TYPE_NUMBER,
    TYPE_STRING,
    build_type_registry,
)
from dioptra.task_engine.types import (
    SimpleType,
    StructuredType,
    StructureType,
    TypeStructure,
    UnionType,
)


def test_builtin_types() -> None:
    types: dict = {}

    type_reg = build_type_registry(types)

    string_type = type_reg["string"]
    int_type = type_reg["integer"]
    number_type = type_reg["number"]
    bool_type = type_reg["boolean"]
    null_type = type_reg["null"]
    any_type = type_reg["any"]

    assert string_type == TYPE_STRING
    assert int_type == TYPE_INTEGER
    assert number_type == TYPE_NUMBER
    assert bool_type == TYPE_BOOLEAN
    assert null_type == TYPE_NULL
    assert any_type == TYPE_ANY

    assert int_type.is_subtype_of(number_type)


def test_build_simple_type() -> None:
    types = {"A": None, "B": {"is_a": "A"}}

    type_reg = build_type_registry(types)

    a_type = type_reg["A"]
    b_type = type_reg["B"]

    assert a_type == SimpleType("A")
    assert b_type == SimpleType("B", super_type=a_type)

    assert b_type.is_subtype_of(a_type)


def test_build_list_type() -> None:
    types = {"A": None, "list_of_a": {"list": "A"}}

    type_reg = build_type_registry(types)

    a_type = type_reg["A"]
    list_of_a_type = type_reg["list_of_a"]

    assert a_type == SimpleType("A")
    assert list_of_a_type == StructuredType(
        TypeStructure(StructureType.LIST, a_type), name="list_of_a"
    )


def test_build_tuple_type() -> None:
    types = {"A": None, "B": None, "tuple_a_b": {"tuple": ["A", "B"]}}

    type_reg = build_type_registry(types)

    a_type = type_reg["A"]
    b_type = type_reg["B"]
    tuple_a_b_type = type_reg["tuple_a_b"]

    assert tuple_a_b_type == StructuredType(
        TypeStructure(StructureType.TUPLE, [a_type, b_type]), name="tuple_a_b"
    )


def test_build_mapping_type_enum() -> None:
    types = {"A": None, "B": None, "mapping_a_b": {"mapping": {"foo": "A", "bar": "B"}}}

    type_reg = build_type_registry(types)

    a_type = type_reg["A"]
    b_type = type_reg["B"]
    mapping_a_b_type = type_reg["mapping_a_b"]

    assert mapping_a_b_type == StructuredType(
        TypeStructure(StructureType.MAPPING, {"foo": a_type, "bar": b_type}),
        name="mapping_a_b",
    )


def test_build_mapping_type_key_value() -> None:
    types = {
        "A": None,
        "mapping_string_a": {"mapping": ["string", "A"]},
        "mapping_integer_a": {"mapping": ["integer", "A"]},
    }

    type_reg = build_type_registry(types)

    a_type = type_reg["A"]
    mapping_string_a_type = type_reg["mapping_string_a"]
    mapping_integer_a_type = type_reg["mapping_integer_a"]

    expected_mapping_string_a_type = StructuredType(
        TypeStructure(StructureType.MAPPING, [TYPE_STRING, a_type]),
        name="mapping_string_a",
    )

    expected_mapping_integer_a_type = StructuredType(
        TypeStructure(StructureType.MAPPING, [TYPE_INTEGER, a_type]),
        name="mapping_integer_a",
    )

    assert mapping_string_a_type == expected_mapping_string_a_type
    assert mapping_integer_a_type == expected_mapping_integer_a_type


def test_build_union_type() -> None:
    types = {"A": None, "B": None, "union_a_b": {"union": ["A", "B"]}}

    type_reg = build_type_registry(types)

    a_type = type_reg["A"]
    b_type = type_reg["B"]
    union_a_b = type_reg["union_a_b"]

    assert union_a_b == UnionType([a_type, b_type], name="union_a_b")


def test_build_nested_type() -> None:
    types = {
        "A": None,
        "nested_type": {"mapping": ["string", {"list": {"tuple": ["A", "number"]}}]},
    }

    type_reg = build_type_registry(types)
    a_type = type_reg["A"]
    nested_type = type_reg["nested_type"]

    expected_type = StructuredType(
        TypeStructure(
            StructureType.MAPPING,
            [
                TYPE_STRING,
                StructuredType(
                    TypeStructure(
                        StructureType.LIST,
                        StructuredType(
                            TypeStructure(StructureType.TUPLE, [a_type, TYPE_NUMBER])
                        ),
                    )
                ),
            ],
        ),
        name="nested_type",
    )

    # This will not actually check structure, since both types are named.
    assert nested_type == expected_type

    # This will check structure, and all sub-structure in this case uses
    # anonymous types, so it's a better test of processing complex nested
    # structures/types.
    assert nested_type.structure == expected_type.structure


def test_build_mapping_type_invalid_key_type() -> None:
    types = {"A": None, "bad_mapping_type": {"mapping": ["A", "integer"]}}

    # The key type in a key/value type style mapping type must be either
    # string or integer.
    with pytest.raises(InvalidKeyTypeError) as e:
        build_type_registry(types)

    assert e.value.invalid_key_type == SimpleType("A")


def test_too_many_structure_types() -> None:
    types = {"A": None, "bad": {"list": "A", "tuple": ["A", "number"]}}

    with pytest.raises(TooManyTypeStructuresError) as e:
        build_type_registry(types)

    assert e.value.structure_types == [StructureType.LIST, StructureType.TUPLE]


def test_non_simple_has_supertype() -> None:
    types = {
        "A": None,
        "B": None,
        "bad_list": {
            "list": "A",
            "is_a": "B",  # invalid: structured types can't have a supertype
        },
    }

    with pytest.raises(DioptraTypeError):
        build_type_registry(types)


def test_union_and_structured() -> None:
    types = {
        "A": None,
        "B": None,
        "bad_type": {
            "union": ["A", "B"],
            "tuple": ["A", "B"],  # invalid: a type can't be both union and
        },  # structured
    }

    with pytest.raises(DioptraTypeError):
        build_type_registry(types)


def test_non_simple_supertype() -> None:
    types = {
        "A": None,
        "list_of_a": {"list": "A"},
        "bad_simple": {
            # invalid: supertypes must be simple
            "is_a": "list_of_a"
        },
    }

    with pytest.raises(NonSimpleSuperTypeError) as e:
        build_type_registry(types)

    assert e.value.super_type_name == "list_of_a"


def test_type_not_found() -> None:
    types = {"list_of_a": {"list": "A"}}

    with pytest.raises(TypeNotFoundError) as e:
        build_type_registry(types)

    assert e.value.type_name == "A"


def test_type_reference_cycle() -> None:
    types: Mapping[str, Any] = {"A": {"is_a": "A"}}

    with pytest.raises(TypeReferenceCycleError) as e:
        build_type_registry(types)

    assert e.value.cycle == ["A", "A"]

    types = {
        "A": {"list": "B"},
        "B": {"tuple": ["string", "C"]},
        "C": {"mapping": {"foo": "A"}},
    }

    with pytest.raises(TypeReferenceCycleError) as e:
        build_type_registry(types)

    assert e.value.cycle == ["A", "C", "B", "A"]


def test_redefine_builtin_type() -> None:
    types = {"A": None, "integer": {"list": "A"}}

    with pytest.raises(BuiltinTypeRedefinitionError) as e:
        build_type_registry(types)

    assert e.value.builtin_type_name == "integer"


def test_anonymous_simple_type() -> None:
    types = {
        # In normal use, this would actually produce a semantic validation
        # error due to the non-string key, before we ever tried to build a type
        # out of it.
        None: {}
    }

    with pytest.raises(AnonymousSimpleTypeError):
        build_type_registry(types)

    types = {
        None: {
            # Since there is no union or structure detected in this definition,
            # it is considered a simple type by build_type_registry().  In
            # reality, this would not pass schema validation.
            "foo": 1
        }
    }

    with pytest.raises(AnonymousSimpleTypeError):
        build_type_registry(types)
