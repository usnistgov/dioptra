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
"""Check type compatibility, literal type inference, and workflow validation."""

from typing import Any

import pytest

from dioptra.task_engine.issues import IssueSeverity, IssueType
from dioptra.task_engine.type_registry import (
    TYPE_ANY,
    TYPE_BOOLEAN,
    TYPE_INTEGER,
    TYPE_NULL,
    TYPE_NUMBER,
    TYPE_STRING,
)
from dioptra.task_engine.type_validation import (
    _infer_type,
    _types_compatible,
    check_types,
)
from dioptra.task_engine.type_validation_state import TypeValidationState
from dioptra.task_engine.types import (
    SimpleType,
    StructuredType,
    StructureType,
    TypeStructure,
    UnionType,
)
from dioptra.task_engine.validation import validate


def assert_compatibility(config: dict[str, Any], compatible: bool) -> None:
    """Check whether workflow validation gives the expected type result.

    Args:
        config: The workflow to validate.
        compatible: True if validation should find no issues. False if it
            should report exactly one incompatible-type error.

    Raises:
        AssertionError: Validation produced a different result.
    """
    issues = validate(config)
    if compatible:
        assert issues == []
    else:
        assert len(issues) == 1
        assert issues[0].type is IssueType.TYPE
        assert issues[0].severity is IssueSeverity.ERROR
        assert "incompatible" in issues[0].message


def test_simple_simple_compatibility() -> None:
    """Simple types match by name and follow the direction of inheritance.

    Two separately created types named A should match. A subtype can supply its
    parent, while an unrelated type or a parent supplied for a subtype should
    fail.
    """
    state = TypeValidationState()
    a_type1 = SimpleType("A")
    a_type2 = SimpleType("A")
    b_type = SimpleType("B")
    super_type = SimpleType("super")
    sub_type = SimpleType("sub", super_type=super_type)

    assert _types_compatible(a_type1, a_type2, state)
    assert _types_compatible(sub_type, super_type, state)
    assert not _types_compatible(a_type1, b_type, state)
    assert not _types_compatible(super_type, sub_type, state)


@pytest.mark.parametrize(
    "incompat_type",
    [
        StructuredType(TypeStructure(StructureType.LIST, SimpleType("A"))),
        StructuredType(
            TypeStructure(StructureType.TUPLE, [SimpleType("A"), SimpleType("B")])
        ),
        StructuredType(
            TypeStructure(
                StructureType.MAPPING, {"a": SimpleType("A"), "b": SimpleType("B")}
            )
        ),
        StructuredType(
            TypeStructure(StructureType.MAPPING, [TYPE_STRING, SimpleType("A")])
        ),
    ],
)
def test_simple_structured_compatibility(incompat_type) -> None:
    """A simple type and a collection are incompatible in either direction.

    Even when the collection contains values of the simple type, the value a task
    receives would have a different kind of structure.
    """
    state = TypeValidationState()
    a_type = SimpleType("A")

    assert not _types_compatible(a_type, incompat_type, state)
    assert not _types_compatible(incompat_type, a_type, state)


def test_list_list_compatibility() -> None:
    """A list can supply a list input when its element type fits.

    A list of a subtype can supply a list of its parent type. Reversing that
    connection would allow elements the input cannot accept.
    """
    state = TypeValidationState()
    a_type = SimpleType("A")
    b_type = SimpleType("B", super_type=a_type)

    list_a = StructuredType(TypeStructure(StructureType.LIST, a_type))

    list_b = StructuredType(TypeStructure(StructureType.LIST, b_type))

    assert _types_compatible(list_a, list_a, state)
    assert _types_compatible(list_b, list_b, state)
    assert _types_compatible(list_b, list_a, state)
    assert not _types_compatible(list_a, list_b, state)


def test_list_tuple_compatibility() -> None:
    """A tuple can supply a list input when every position fits.

    Both tuple members fit a list of their parent type. Only one fits a list
    restricted to the first subtype. A list cannot guarantee the positions
    required by the tuple.
    """
    state = TypeValidationState()
    a_type = SimpleType("A")
    b1_type = SimpleType("B1", super_type=a_type)
    b2_type = SimpleType("B2", super_type=a_type)

    list_a = StructuredType(TypeStructure(StructureType.LIST, a_type))

    list_b1 = StructuredType(TypeStructure(StructureType.LIST, b1_type))

    tuple_b = StructuredType(TypeStructure(StructureType.TUPLE, [b1_type, b2_type]))

    assert _types_compatible(tuple_b, list_a, state)
    assert not _types_compatible(list_a, tuple_b, state)
    assert not _types_compatible(tuple_b, list_b1, state)
    assert not _types_compatible(list_b1, tuple_b, state)


def test_tuple_tuple_compatibility() -> None:
    """Tuple types must agree on length and match at every position.

    A subtype can supply a position that expects its parent. An extra position or
    an incompatible member prevents a match, and an empty tuple matches another
    empty tuple.
    """
    state = TypeValidationState()
    a_type = SimpleType("A")
    b1_type = SimpleType("B1", super_type=a_type)
    b2_type = SimpleType("B2", super_type=a_type)
    c_type = SimpleType("C")

    tuple_a = StructuredType(TypeStructure(StructureType.TUPLE, [a_type]))

    tuple_a_a = StructuredType(TypeStructure(StructureType.TUPLE, [a_type, a_type]))

    tuple_b_b = StructuredType(TypeStructure(StructureType.TUPLE, [b1_type, b2_type]))

    tuple_b_b_b = StructuredType(
        TypeStructure(StructureType.TUPLE, [b1_type, b2_type, b2_type])
    )

    tuple_b_c = StructuredType(
        TypeStructure(StructureType.TUPLE, [b1_type, b2_type, c_type])
    )

    empty_tuple = StructuredType(TypeStructure(StructureType.TUPLE, []))

    assert not _types_compatible(tuple_b_b, tuple_a, state)
    assert not _types_compatible(tuple_a, tuple_b_b, state)
    assert _types_compatible(tuple_b_b, tuple_a_a, state)
    assert not _types_compatible(tuple_b_b, tuple_b_b_b, state)
    assert not _types_compatible(tuple_b_b_b, tuple_b_c, state)
    assert _types_compatible(tuple_b_c, tuple_b_c, state)
    assert _types_compatible(empty_tuple, empty_tuple, state)
    assert not _types_compatible(empty_tuple, tuple_a, state)
    assert not _types_compatible(tuple_a, empty_tuple, state)


def test_map_enum_map_enum_compatibility() -> None:
    """Mappings with declared fields must agree on the keys and their value types.

    A field can supply a more general value type under the same key. Missing or
    different keys prevent a match, even when the values would fit.
    """
    state = TypeValidationState()
    a_type = SimpleType("A")
    b_type = SimpleType("B", super_type=a_type)
    c_type = SimpleType("C")

    map_a = StructuredType(TypeStructure(StructureType.MAPPING, {"a": a_type}))

    map_b = StructuredType(TypeStructure(StructureType.MAPPING, {"b": b_type}))

    map_b_keyed_a = StructuredType(TypeStructure(StructureType.MAPPING, {"a": b_type}))

    map_c = StructuredType(TypeStructure(StructureType.MAPPING, {"c": c_type}))

    map_a_c = StructuredType(
        TypeStructure(StructureType.MAPPING, {"a": a_type, "c": c_type})
    )

    empty_map = StructuredType(TypeStructure(StructureType.MAPPING, {}))

    assert _types_compatible(map_a, map_a, state)
    assert _types_compatible(map_b_keyed_a, map_a, state)
    assert not _types_compatible(map_b, map_a, state)
    assert not _types_compatible(map_a, map_b_keyed_a, state)
    assert not _types_compatible(map_a, map_b, state)
    assert not _types_compatible(map_a, map_c, state)
    assert not _types_compatible(map_b, map_c, state)
    assert not _types_compatible(map_a, map_a_c, state)
    assert not _types_compatible(map_b, map_a_c, state)
    assert not _types_compatible(map_c, map_a_c, state)
    assert _types_compatible(empty_map, empty_map, state)
    assert not _types_compatible(empty_map, map_a, state)
    assert not _types_compatible(map_a, empty_map, state)


def test_map_kv_map_kv_compatibility() -> None:
    """Mappings declared by key and value type must match on both.

    A mapping with more specific values can supply one that accepts their parent
    type. Different key types or unrelated value types prevent a match.
    """
    state = TypeValidationState()
    a_type = SimpleType("A")
    b_type = SimpleType("B", super_type=a_type)
    c_type = SimpleType("C")

    map_string_a = StructuredType(
        TypeStructure(StructureType.MAPPING, [TYPE_STRING, a_type])
    )

    map_string_b = StructuredType(
        TypeStructure(StructureType.MAPPING, [TYPE_STRING, b_type])
    )

    map_string_c = StructuredType(
        TypeStructure(StructureType.MAPPING, [TYPE_STRING, c_type])
    )

    map_int_b = StructuredType(
        TypeStructure(StructureType.MAPPING, [TYPE_INTEGER, b_type])
    )

    assert _types_compatible(map_string_a, map_string_a, state)
    assert _types_compatible(map_string_b, map_string_a, state)
    assert not _types_compatible(map_string_a, map_string_b, state)
    assert not _types_compatible(map_string_c, map_string_a, state)
    assert not _types_compatible(map_int_b, map_string_b, state)
    assert _types_compatible(map_int_b, map_int_b, state)


def test_map_kv_map_enum_compatibility() -> None:
    """Named fields can satisfy a mapping input with a common value type.

    Every field has a string key and its value must fit the input. In the other
    direction, a general mapping cannot guarantee a particular set of fields.
    """
    state = TypeValidationState()
    a_type = SimpleType("A")
    b_type = SimpleType("B", super_type=a_type)

    map_a = StructuredType(TypeStructure(StructureType.MAPPING, {"a": a_type}))

    map_b = StructuredType(TypeStructure(StructureType.MAPPING, {"b": b_type}))

    empty_map = StructuredType(TypeStructure(StructureType.MAPPING, {}))

    map_string_a = StructuredType(
        TypeStructure(StructureType.MAPPING, [TYPE_STRING, a_type])
    )

    map_string_b = StructuredType(
        TypeStructure(StructureType.MAPPING, [TYPE_STRING, b_type])
    )

    map_int_a = StructuredType(
        TypeStructure(StructureType.MAPPING, [TYPE_INTEGER, a_type])
    )

    assert _types_compatible(map_a, map_string_a, state)
    assert not _types_compatible(map_string_a, map_a, state)
    assert _types_compatible(map_b, map_string_a, state)
    assert not _types_compatible(map_string_b, map_a, state)
    assert not _types_compatible(map_b, map_int_a, state)
    assert _types_compatible(empty_map, map_string_a, state)
    assert _types_compatible(empty_map, map_string_b, state)
    assert not _types_compatible(empty_map, map_int_a, state)
    assert not _types_compatible(map_string_a, empty_map, state)
    assert not _types_compatible(map_int_a, empty_map, state)


def test_map_other_structured_compatibility() -> None:
    """A mapping cannot supply a list or tuple input, or the reverse.

    Even when their values have the same type, a mapping uses keys and the other
    collections use positions. This applies to both forms of mapping.
    """
    state = TypeValidationState()
    a_type = SimpleType("A")

    map_a = StructuredType(TypeStructure(StructureType.MAPPING, {"a": a_type}))

    map_string_a = StructuredType(
        TypeStructure(StructureType.MAPPING, [TYPE_STRING, a_type])
    )

    list_a = StructuredType(TypeStructure(StructureType.LIST, a_type))

    tuple_a = StructuredType(TypeStructure(StructureType.TUPLE, [a_type]))

    assert not _types_compatible(map_a, list_a, state)
    assert not _types_compatible(list_a, map_a, state)
    assert not _types_compatible(map_a, tuple_a, state)
    assert not _types_compatible(tuple_a, map_a, state)
    assert not _types_compatible(map_string_a, list_a, state)
    assert not _types_compatible(list_a, map_string_a, state)
    assert not _types_compatible(map_string_a, tuple_a, state)
    assert not _types_compatible(tuple_a, map_string_a, state)


def test_union_compatibility() -> None:
    """Every possible output type must fit the input.

    For a union input, each possible output only needs to match one member. A
    subtype can therefore fit a union containing its parent, but the reverse can
    fail.
    """
    state = TypeValidationState()
    a_type = SimpleType("A")
    b_type = SimpleType("B", super_type=a_type)
    c_type = SimpleType("C")

    union_a = UnionType([a_type])
    union_b = UnionType([b_type])
    union_a_c = UnionType([a_type, c_type])

    assert _types_compatible(a_type, union_a, state)
    assert _types_compatible(b_type, union_a, state)
    assert not _types_compatible(c_type, union_a, state)
    assert _types_compatible(b_type, union_a_c, state)
    assert _types_compatible(union_a, a_type, state)
    assert _types_compatible(union_b, a_type, state)
    assert _types_compatible(union_a, union_a, state)
    assert _types_compatible(union_b, union_a, state)
    assert not _types_compatible(union_a, union_b, state)
    assert not _types_compatible(union_a_c, union_b, state)


@pytest.mark.parametrize(
    "type_named, type_anon",
    [
        (
            StructuredType(
                TypeStructure(StructureType.LIST, SimpleType("A")), name="list_a"
            ),
            StructuredType(TypeStructure(StructureType.LIST, SimpleType("A"))),
        ),
        (
            StructuredType(
                TypeStructure(StructureType.TUPLE, [SimpleType("A")]), name="tuple_a"
            ),
            StructuredType(TypeStructure(StructureType.TUPLE, [SimpleType("A")])),
        ),
        (
            StructuredType(
                TypeStructure(StructureType.MAPPING, {"a": SimpleType("A")}),
                name="mapping_a_enum",
            ),
            StructuredType(
                TypeStructure(StructureType.MAPPING, {"a": SimpleType("A")})
            ),
        ),
        (
            StructuredType(
                TypeStructure(StructureType.MAPPING, [TYPE_STRING, SimpleType("A")]),
                name="mapping_a_key_value",
            ),
            StructuredType(
                TypeStructure(StructureType.MAPPING, [TYPE_STRING, SimpleType("A")])
            ),
        ),
    ],
)
def test_named_anon_type_compatibility(type_named, type_anon) -> None:
    """A named collection can match the same structure defined inline.

    For lists, tuples, and both kinds of mapping, each type should match itself
    and its counterpart in either direction.
    """
    state = TypeValidationState()
    assert _types_compatible(type_named, type_named, state)
    assert _types_compatible(type_anon, type_anon, state)
    assert _types_compatible(type_named, type_anon, state)
    assert _types_compatible(type_anon, type_named, state)


def test_named_type_compatibility() -> None:
    """Names distinguish named lists, while union compatibility depends on members.

    Two differently named lists with identical elements should be incompatible.
    Two differently named unions with identical members should match.
    """
    state = TypeValidationState()
    a_type = SimpleType("A")
    list_a1 = StructuredType(TypeStructure(StructureType.LIST, a_type), name="name1")

    list_a2 = StructuredType(TypeStructure(StructureType.LIST, a_type), name="name2")

    # list structure is compatible, but names are not equal, so the types are
    # incompatible.
    assert not _types_compatible(list_a1, list_a2, state)

    union_a1 = UnionType([a_type], name="name1")
    union_a2 = UnionType([a_type], name="name2")

    # ... but unions are an exception.  Their names are ignored and only their
    # members are considered.
    assert _types_compatible(union_a1, union_a2, state)


def test_any_compatibility() -> None:
    """An input declared as any accepts values of every type.

    An output declared as any can supply an unrestricted input or a union that
    includes any. It cannot guarantee the specific type a narrower input
    requires.
    """
    state = TypeValidationState()
    a_type = SimpleType("A")
    union_a_any = UnionType([a_type, TYPE_ANY])

    assert _types_compatible(a_type, TYPE_ANY, state)
    assert _types_compatible(TYPE_ANY, TYPE_ANY, state)
    assert not _types_compatible(TYPE_ANY, a_type, state)
    assert _types_compatible(union_a_any, union_a_any, state)
    assert _types_compatible(TYPE_ANY, union_a_any, state)
    assert _types_compatible(union_a_any, TYPE_ANY, state)
    assert _types_compatible(a_type, union_a_any, state)


@pytest.mark.parametrize(
    "value, expected_type",
    [
        (1, TYPE_INTEGER),
        (1.1, TYPE_NUMBER),
        ("foo", TYPE_STRING),
        (True, TYPE_BOOLEAN),
        (None, TYPE_NULL),
        (1 + 2j, TYPE_ANY),
    ],
)
def test_type_inference_simple(value, expected_type) -> None:
    """Infer the built-in Dioptra type for a single Python value.

    Booleans and integers have distinct types. A complex number has no
    corresponding Dioptra type, so its inferred type should be any.
    """
    inferred_type = _infer_type(value, state=TypeValidationState())
    assert inferred_type == expected_type


@pytest.mark.parametrize(
    "value, expected_type",
    [
        ([1], StructuredType(TypeStructure(StructureType.TUPLE, [TYPE_INTEGER]))),
        (
            [1, False],
            StructuredType(
                TypeStructure(StructureType.TUPLE, [TYPE_INTEGER, TYPE_BOOLEAN])
            ),
        ),
        ([], StructuredType(TypeStructure(StructureType.TUPLE, []))),
    ],
)
def test_type_inference_tuple(value, expected_type) -> None:
    """A list literal has a known length and a type at each position.

    The inferred tuple should preserve the order of the integer and boolean
    in a mixed list. An empty list should produce a tuple with no elements.
    """
    inferred_type = _infer_type(value, state=TypeValidationState())
    assert inferred_type == expected_type


@pytest.mark.parametrize(
    "value, expected_type",
    [
        (
            {"a": 1},
            StructuredType(TypeStructure(StructureType.MAPPING, {"a": TYPE_INTEGER})),
        ),
        (
            {"a": "foo", "b": None},
            StructuredType(
                TypeStructure(StructureType.MAPPING, {"a": TYPE_STRING, "b": TYPE_NULL})
            ),
        ),
        (
            {1: "a", 2: "b"},
            StructuredType(
                TypeStructure(StructureType.MAPPING, [TYPE_INTEGER, TYPE_STRING])
            ),
        ),
        (
            {1: "a", 2: True},
            StructuredType(
                TypeStructure(
                    StructureType.MAPPING,
                    [TYPE_INTEGER, UnionType([TYPE_STRING, TYPE_BOOLEAN])],
                )
            ),
        ),
        ({1 + 2j: 1.23, None: "hello"}, TYPE_ANY),
        ({}, StructuredType(TypeStructure(StructureType.MAPPING, {}))),
    ],
)
def test_type_inference_mapping(value, expected_type) -> None:
    """Infer what task inputs a dictionary can supply from its keys and values.

    String keys describe individual fields. Integer keys share a value type,
    which can be a union when the values differ. An empty dictionary has no
    fields, and a dictionary with unsupported key types falls back to any.
    """
    inferred_type = _infer_type(value, state=TypeValidationState())
    assert inferred_type == expected_type


@pytest.mark.parametrize(
    "value,target,compatible",
    [
        (1, "integer", True),
        (1, "number", True),
        (1, "boolean", False),
        (1.1, "number", True),
        (1.1, "integer", False),
        ("foo", "string", True),
        ("foo", "number", False),
        (True, "boolean", True),
        (True, "integer", False),
        (None, "null", True),
        (None, "string", False),
        ([1], {"tuple": ["integer"]}, True),
        ([1, False], {"tuple": ["integer", "boolean"]}, True),
        ([1, False], {"tuple": ["integer", "integer"]}, False),
        ([1, False], {"tuple": ["boolean", "integer"]}, False),
        ([1, 2], {"list": "number"}, True),
        ([1, "text"], {"list": "number"}, False),
        ([], {"list": "number"}, True),
        ([], {"tuple": []}, True),
        ([], {"tuple": ["integer"]}, False),
        ({"a": 1}, {"mapping": {"a": "integer"}}, True),
        ({"a": 1}, {"mapping": {"a": "string"}}, False),
        ({"a": "foo", "b": None}, {"mapping": {"a": "string", "b": "null"}}, True),
        ({"a": "foo", "b": None}, {"mapping": {"a": "string", "b": "string"}}, False),
        ({1: "a", 2: "b"}, {"mapping": ["integer", "string"]}, True),
        (
            {1: "a", 2: True},
            {"mapping": ["integer", {"union": ["string", "boolean"]}]},
            True,
        ),
        ({1: "a", 2: True}, {"mapping": ["integer", "string"]}, False),
        ({}, {"mapping": ["string", "integer"]}, True),
        ({}, {"mapping": {}}, True),
        ({}, {"mapping": ["integer", "integer"]}, False),
        ({}, {"mapping": {"a": "integer"}}, False),
    ],
)
def test_literal_argument_compatibility(value, target, compatible) -> None:
    """A value supplied directly in a step must match the task input.

    For a collection, the check also depends on its contents. A list of numbers
    fits a numeric list input, for example, but a list containing text should
    produce a type error.
    """
    config = {
        "types": {"Target": {"union": [target]}},
        "tasks": {
            "consume": {"plugin": "example.consume", "inputs": [{"value": "Target"}]}
        },
        "graph": {"step": {"consume": [value]}},
    }
    assert_compatibility(config, compatible)


@pytest.mark.parametrize("value", [1 + 2j, {1 + 2j: 1.23, None: "hello"}])
@pytest.mark.parametrize("target,compatible", [("any", True), ("string", False)])
def test_python_values_without_declared_types(value, target, compatible) -> None:
    """An input declared as any can accept Python values without a Dioptra type.

    Python callers can supply a complex number or a dictionary with a complex key
    directly to the type checker. Either value should pass for an unrestricted
    input and fail for a string input.
    """
    config = {
        "tasks": {
            "consume": {"plugin": "example.consume", "inputs": [{"value": target}]}
        },
        "graph": {"step": {"consume": [value]}},
    }
    issues = check_types(config)
    if compatible:
        assert issues == []
    else:
        assert len(issues) == 1
        assert "incompatible" in issues[0].message


@pytest.mark.parametrize(
    "other",
    [
        SimpleType("A"),
        UnionType([SimpleType("A"), SimpleType("B")]),
        StructuredType(TypeStructure(StructureType.LIST, SimpleType("A"))),
        StructuredType(
            TypeStructure(StructureType.TUPLE, [SimpleType("A"), SimpleType("B")])
        ),
        StructuredType(
            TypeStructure(
                StructureType.MAPPING, {"a": SimpleType("A"), "b": SimpleType("B")}
            )
        ),
        StructuredType(
            TypeStructure(
                StructureType.MAPPING, [SimpleType("string"), SimpleType("A")]
            )
        ),
    ],
)
def test_empty_union_compatibility(other) -> None:
    """An empty union has no possible output values.

    The registry cannot build an empty union, so this case uses the type
    checker directly. An empty union as an output fits any of the inputs
    tested here. As an input, it accepts only the empty union in these cases.
    """
    empty = UnionType([])
    assert _types_compatible(empty, empty, TypeValidationState())
    assert _types_compatible(empty, other, TypeValidationState())
    assert not _types_compatible(other, empty, TypeValidationState())


@pytest.mark.parametrize(
    "type_name,value,compatible",
    [
        ("integer", 1, True),
        ("number", 1.2, True),
        ("number", 1, True),
        ("string", "abc", True),
        ("boolean", True, True),
        ("null", None, True),
        ("integer", "not_an_int", False),
        ("integer", 1.2, False),
        ("number", None, False),
        ("null", 1, False),
        ("string", 1, False),
        ("boolean", 1, False),
    ],
)
def test_global_parameter_defaults(type_name, value, compatible) -> None:
    """A global parameter default must fit its declared type.

    The workflow never uses the parameter. Validation should still accept a
    matching default and report a type error for an incompatible one.
    """
    config = {
        "parameters": {"value": {"type": type_name, "default": value}},
        "tasks": {"consume": {"plugin": "example.consume"}},
        "graph": {"step": {"consume": []}},
    }
    assert_compatibility(config, compatible)


@pytest.mark.parametrize(
    "inputs,invocation,compatible",
    [
        ([{"value": "integer"}], {"consume": "foo"}, False),
        ([{"value": "number"}], {"consume": 1}, True),
        ([{"value": "integer"}], {"consume": {"value": "foo"}}, False),
        ([{"value": "string"}], {"consume": {"value": "foo"}}, True),
        (
            [
                {"first": "integer"},
                {"name": "second", "type": "boolean", "required": True},
            ],
            {"task": "consume", "args": "foo", "kwargs": {"second": 1}},
            False,
        ),
        (
            [
                {"first": "boolean"},
                {"name": "second", "type": "null", "required": True},
            ],
            {"task": "consume", "args": True, "kwargs": {"second": None}},
            True,
        ),
    ],
)
def test_invocation_argument_forms(inputs, invocation, compatible) -> None:
    """Task arguments must match their inputs however the step supplies them.

    The same type rules apply to arguments supplied by position, by name, or both.
    Matching values should pass and incompatible values should produce type
    errors.
    """
    config = {
        "tasks": {"consume": {"plugin": "example.consume", "inputs": inputs}},
        "graph": {"step": invocation},
    }
    issues = validate(config)
    if compatible:
        assert issues == []
    else:
        assert issues
        assert all(issue.type is IssueType.TYPE for issue in issues)
        assert all("incompatible" in issue.message for issue in issues)


@pytest.mark.parametrize(
    "source_types,target_types,compatible",
    [
        (["number", "string"], ["integer", "null"], False),
        (["integer", "string"], ["number", "any"], True),
    ],
)
def test_hybrid_invocation_with_references(
    source_types, target_types, compatible
) -> None:
    """A step can use earlier outputs as both positional and named arguments.

    The consuming step takes two outputs from the same earlier step. Compatible
    output types should pass. When both types are wrong, validation should report
    two errors.
    """
    config = {
        "tasks": {
            "produce": {
                "plugin": "example.produce",
                "outputs": [{"first": source_types[0]}, {"second": source_types[1]}],
            },
            "consume": {
                "plugin": "example.consume",
                "inputs": [{"first": target_types[0]}, {"second": target_types[1]}],
            },
        },
        "graph": {
            "produce": {"produce": []},
            "consume": {
                "task": "consume",
                "args": "$produce.first",
                "kwargs": {"second": "$produce.second"},
            },
        },
    }
    issues = validate(config)
    if compatible:
        assert issues == []
    else:
        assert len(issues) == 2
        assert all(issue.type is IssueType.TYPE for issue in issues)
        assert all("incompatible" in issue.message for issue in issues)
