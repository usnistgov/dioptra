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

from dioptra.task_engine.type_registry import (
    TYPE_ANY,
    TYPE_BOOLEAN,
    TYPE_INTEGER,
    TYPE_NULL,
    TYPE_NUMBER,
    TYPE_STRING,
)
from dioptra.task_engine.type_validation import _infer_type, _types_compatible
from dioptra.task_engine.types import (
    SimpleType,
    StructuredType,
    StructureType,
    TypeStructure,
    UnionType,
)
from dioptra.task_engine.validation import is_valid


def test_simple_simple_compatibility() -> None:
    a_type1 = SimpleType("A")
    a_type2 = SimpleType("A")
    b_type = SimpleType("B")
    super_type = SimpleType("super")
    sub_type = SimpleType("sub", super_type=super_type)

    assert _types_compatible(a_type1, a_type2)
    assert _types_compatible(sub_type, super_type)
    assert not _types_compatible(a_type1, b_type)
    assert not _types_compatible(super_type, sub_type)


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
    a_type = SimpleType("A")

    assert not _types_compatible(a_type, incompat_type)
    assert not _types_compatible(incompat_type, a_type)


def test_list_list_compatibility() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B", super_type=a_type)

    list_a = StructuredType(TypeStructure(StructureType.LIST, a_type))

    list_b = StructuredType(TypeStructure(StructureType.LIST, b_type))

    assert _types_compatible(list_a, list_a)
    assert _types_compatible(list_b, list_b)
    assert _types_compatible(list_b, list_a)
    assert not _types_compatible(list_a, list_b)


def test_list_tuple_compatibility() -> None:
    a_type = SimpleType("A")
    b1_type = SimpleType("B1", super_type=a_type)
    b2_type = SimpleType("B2", super_type=a_type)

    list_a = StructuredType(TypeStructure(StructureType.LIST, a_type))

    list_b1 = StructuredType(TypeStructure(StructureType.LIST, b1_type))

    tuple_b = StructuredType(TypeStructure(StructureType.TUPLE, [b1_type, b2_type]))

    assert _types_compatible(tuple_b, list_a)
    assert not _types_compatible(list_a, tuple_b)
    assert not _types_compatible(tuple_b, list_b1)
    assert not _types_compatible(list_b1, tuple_b)


def test_tuple_tuple_compatibility() -> None:
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

    assert not _types_compatible(tuple_b_b, tuple_a)
    assert not _types_compatible(tuple_a, tuple_b_b)
    assert _types_compatible(tuple_b_b, tuple_a_a)
    assert not _types_compatible(tuple_b_b, tuple_b_b_b)
    assert not _types_compatible(tuple_b_b_b, tuple_b_c)
    assert _types_compatible(tuple_b_c, tuple_b_c)
    assert _types_compatible(empty_tuple, empty_tuple)
    assert not _types_compatible(empty_tuple, tuple_a)
    assert not _types_compatible(tuple_a, empty_tuple)


def test_map_enum_map_enum_compatibility() -> None:
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

    assert _types_compatible(map_a, map_a)
    assert _types_compatible(map_b_keyed_a, map_a)
    assert not _types_compatible(map_b, map_a)
    assert not _types_compatible(map_a, map_b_keyed_a)
    assert not _types_compatible(map_a, map_b)
    assert not _types_compatible(map_a, map_c)
    assert not _types_compatible(map_b, map_c)
    assert not _types_compatible(map_a, map_a_c)
    assert not _types_compatible(map_b, map_a_c)
    assert not _types_compatible(map_c, map_a_c)
    assert _types_compatible(empty_map, empty_map)
    assert not _types_compatible(empty_map, map_a)
    assert not _types_compatible(map_a, empty_map)


def test_map_kv_map_kv_compatibility() -> None:
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

    assert _types_compatible(map_string_a, map_string_a)
    assert _types_compatible(map_string_b, map_string_a)
    assert not _types_compatible(map_string_a, map_string_b)
    assert not _types_compatible(map_string_c, map_string_a)
    assert not _types_compatible(map_int_b, map_string_b)
    assert _types_compatible(map_int_b, map_int_b)


def test_map_kv_map_enum_compatibility() -> None:
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

    assert _types_compatible(map_a, map_string_a)
    assert not _types_compatible(map_string_a, map_a)
    assert _types_compatible(map_b, map_string_a)
    assert not _types_compatible(map_string_b, map_a)
    assert not _types_compatible(map_b, map_int_a)
    assert _types_compatible(empty_map, map_string_a)
    assert _types_compatible(empty_map, map_string_b)
    assert not _types_compatible(empty_map, map_int_a)
    assert not _types_compatible(map_string_a, empty_map)
    assert not _types_compatible(map_int_a, empty_map)


def test_map_other_structured_compatibility() -> None:
    a_type = SimpleType("A")

    map_a = StructuredType(TypeStructure(StructureType.MAPPING, {"a": a_type}))

    map_string_a = StructuredType(
        TypeStructure(StructureType.MAPPING, [TYPE_STRING, a_type])
    )

    list_a = StructuredType(TypeStructure(StructureType.LIST, a_type))

    tuple_a = StructuredType(TypeStructure(StructureType.TUPLE, [a_type]))

    assert not _types_compatible(map_a, list_a)
    assert not _types_compatible(list_a, map_a)
    assert not _types_compatible(map_a, tuple_a)
    assert not _types_compatible(tuple_a, map_a)
    assert not _types_compatible(map_string_a, list_a)
    assert not _types_compatible(list_a, map_string_a)
    assert not _types_compatible(map_string_a, tuple_a)
    assert not _types_compatible(tuple_a, map_string_a)


def test_union_compatibility() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B", super_type=a_type)
    c_type = SimpleType("C")

    union_a = UnionType([a_type])
    union_b = UnionType([b_type])
    union_a_c = UnionType([a_type, c_type])

    assert _types_compatible(a_type, union_a)
    assert _types_compatible(b_type, union_a)
    assert not _types_compatible(c_type, union_a)
    assert _types_compatible(b_type, union_a_c)
    assert _types_compatible(union_a, a_type)
    assert _types_compatible(union_b, a_type)
    assert _types_compatible(union_a, union_a)
    assert _types_compatible(union_b, union_a)
    assert not _types_compatible(union_a, union_b)
    assert not _types_compatible(union_a_c, union_b)


def test_empty_union_compatibility() -> None:
    a_type = SimpleType("A")
    b_type = SimpleType("B")

    union_a_b = UnionType([a_type, b_type])
    empty_union = UnionType([])
    list_a = StructuredType(TypeStructure(StructureType.LIST, a_type))
    tuple_a_b = StructuredType(TypeStructure(StructureType.TUPLE, [a_type, b_type]))
    enum_map_a_b = StructuredType(
        TypeStructure(StructureType.MAPPING, {"a": a_type, "b": b_type})
    )
    kv_map_a_b = StructuredType(
        TypeStructure(StructureType.MAPPING, [TYPE_STRING, a_type])
    )

    # Treat empty union like an "empty set": it is compatible with all,
    # and nothing except itself is compatible with it.
    assert _types_compatible(empty_union, empty_union)
    assert _types_compatible(empty_union, union_a_b)
    assert _types_compatible(empty_union, a_type)
    assert _types_compatible(empty_union, list_a)
    assert _types_compatible(empty_union, tuple_a_b)
    assert _types_compatible(empty_union, enum_map_a_b)
    assert _types_compatible(empty_union, kv_map_a_b)
    assert not _types_compatible(a_type, empty_union)
    assert not _types_compatible(union_a_b, empty_union)
    assert not _types_compatible(list_a, empty_union)
    assert not _types_compatible(tuple_a_b, empty_union)
    assert not _types_compatible(enum_map_a_b, empty_union)
    assert not _types_compatible(kv_map_a_b, empty_union)


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
    assert _types_compatible(type_named, type_named)
    assert _types_compatible(type_anon, type_anon)
    assert _types_compatible(type_named, type_anon)
    assert _types_compatible(type_anon, type_named)


def test_named_type_compatibility() -> None:
    a_type = SimpleType("A")
    list_a1 = StructuredType(TypeStructure(StructureType.LIST, a_type), name="name1")

    list_a2 = StructuredType(TypeStructure(StructureType.LIST, a_type), name="name2")

    # list structure is compatible, but names are not equal, so the types are
    # incompatible.
    assert not _types_compatible(list_a1, list_a2)

    union_a1 = UnionType([a_type], name="name1")
    union_a2 = UnionType([a_type], name="name2")

    # ... but unions are an exception.  Their names are ignored and only their
    # members are considered.
    assert _types_compatible(union_a1, union_a2)


def test_any_compatibility() -> None:
    a_type = SimpleType("A")
    union_a_any = UnionType([a_type, TYPE_ANY])

    assert _types_compatible(a_type, TYPE_ANY)
    assert _types_compatible(TYPE_ANY, TYPE_ANY)
    assert not _types_compatible(TYPE_ANY, a_type)
    assert _types_compatible(union_a_any, union_a_any)
    assert _types_compatible(TYPE_ANY, union_a_any)
    assert _types_compatible(union_a_any, TYPE_ANY)
    assert _types_compatible(a_type, union_a_any)


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
    inferred_type = _infer_type(value)
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
    inferred_type = _infer_type(value)
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
    inferred_type = _infer_type(value)
    assert inferred_type == expected_type


def test_global_parameter_defaults_good():
    experiment_desc = {
        "parameters": {
            "int": {"type": "integer", "default": 1},
            "number": {"type": "number", "default": 1.2},
            "num_init_with_int": {"type": "number", "default": 1},
            "string": {"type": "string", "default": "abc"},
            "boolean": {"type": "boolean", "default": True},
            "null": {"type": "null", "default": None},
        },
        "tasks": {"foo": {"plugin": "org.example.foo"}},
        "graph": {"step1": {"foo": []}},
    }

    assert is_valid(experiment_desc)


@pytest.mark.parametrize(
    "bad_param",
    [
        {"type": "integer", "default": "not_an_int"},
        {"type": "integer", "default": 1.2},
        {"type": "number", "default": None},
        {"type": "null", "default": 1},
        {"type": "string", "default": 1},
        {"type": "boolean", "default": 1},
    ],
)
def test_global_parameter_defaults_bad(bad_param) -> None:
    experiment_desc = {
        "parameters": {"bad_param": bad_param},
        "tasks": {"foo": {"plugin": "org.example.foo"}},
        "graph": {"step1": {"foo": []}},
    }

    assert not is_valid(experiment_desc)


def test_positional_invocation_type_error() -> None:
    experiment_desc = {
        "tasks": {
            "task1": {"plugin": "org.example.task1", "inputs": [{"in1": "integer"}]}
        },
        "graph": {"step1": {"task1": "foo"}},
    }

    assert not is_valid(experiment_desc)


def test_positional_invocation_type_ok() -> None:
    experiment_desc = {
        "tasks": {
            "task1": {"plugin": "org.example.task1", "inputs": [{"in1": "number"}]}
        },
        "graph": {"step1": {"task1": 1}},
    }

    assert is_valid(experiment_desc)


def test_keyword_invocation_type_error() -> None:
    experiment_desc = {
        "tasks": {
            "task1": {"plugin": "org.example.task1", "inputs": [{"in1": "integer"}]}
        },
        "graph": {"step1": {"task1": {"in1": "foo"}}},
    }

    assert not is_valid(experiment_desc)


def test_keyword_invocation_type_ok() -> None:
    experiment_desc = {
        "tasks": {
            "task1": {"plugin": "org.example.task1", "inputs": [{"in1": "string"}]}
        },
        "graph": {"step1": {"task1": {"in1": "foo"}}},
    }

    assert is_valid(experiment_desc)


def test_hybrid_invocation_type_error() -> None:
    experiment_desc = {
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "inputs": [
                    {"in1": "integer"},
                    {"name": "in2", "type": "boolean", "required": True},
                ],
            }
        },
        "graph": {"step1": {"task": "task1", "args": "foo", "kwargs": {"in2": 1}}},
    }

    assert not is_valid(experiment_desc)


def test_hybrid_invocation_type_ok() -> None:
    experiment_desc = {
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "inputs": [
                    {"in1": "boolean"},
                    {"name": "in2", "type": "null", "required": True},
                ],
            }
        },
        "graph": {"step1": {"task": "task1", "args": True, "kwargs": {"in2": None}}},
    }

    assert is_valid(experiment_desc)


def test_hybrid_invocation_type_error_with_references() -> None:
    experiment_desc = {
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "outputs": [{"out1": "number"}, {"out2": "string"}],
            },
            "task2": {
                "plugin": "org.example.task2",
                "inputs": [{"in1": "integer"}, {"in2": "null"}],
            },
        },
        "graph": {
            "step1": {"task1": []},
            "step2": {
                "task": "task2",
                "args": "$step1.out1",
                "kwargs": {"in2": "$step1.out2"},
            },
        },
    }

    assert not is_valid(experiment_desc)


def test_hybrid_invocation_type_ok_with_references() -> None:
    experiment_desc = {
        "tasks": {
            "task1": {
                "plugin": "org.example.task1",
                "outputs": [{"out1": "integer"}, {"out2": "string"}],
            },
            "task2": {
                "plugin": "org.example.task2",
                "inputs": [{"in1": "number"}, {"in2": "any"}],
            },
        },
        "graph": {
            "step1": {"task1": []},
            "step2": {
                "task": "task2",
                "args": "$step1.out1",
                "kwargs": {"in2": "$step1.out2"},
            },
        },
    }

    assert is_valid(experiment_desc)
