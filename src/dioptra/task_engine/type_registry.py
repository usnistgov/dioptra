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
Build a "type registry", i.e. a mapping from type name to Type instance,
from a set of type definitions.
"""
import graphlib
from collections.abc import Iterable, Iterator, Mapping, MutableMapping, Sequence
from typing import Any, Optional, Union, cast

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
from dioptra.task_engine import types

TYPE_ANY = types.SimpleType("any")
TYPE_NUMBER = types.SimpleType("number")
TYPE_INTEGER = types.SimpleType("integer", super_type=TYPE_NUMBER)
TYPE_STRING = types.SimpleType("string")
TYPE_BOOLEAN = types.SimpleType("boolean")
TYPE_NULL = types.SimpleType("null")


BUILTIN_TYPES = {
    TYPE_ANY.name: TYPE_ANY,
    TYPE_STRING.name: TYPE_STRING,
    TYPE_INTEGER.name: TYPE_INTEGER,
    TYPE_NUMBER.name: TYPE_NUMBER,
    TYPE_BOOLEAN.name: TYPE_BOOLEAN,
    TYPE_NULL.name: TYPE_NULL,
}


# Type aliases for type annotations
_TypeRegistry = Mapping[str, types.Type]
_TypeDefinition = Mapping[str, Any]
_NestedTypeDefOrRef = Union[_TypeDefinition, str]


def _build_mapping_structure(
    map_structure: Union[
        Mapping[str, _NestedTypeDefOrRef], Sequence[_NestedTypeDefOrRef]
    ],
    type_registry: _TypeRegistry,
):
    """
    Build a TypeStructure instance from a definition of a mapping structure.

    Args:
        map_structure: The structure definition
        type_registry: A type registry, used to look up type references

    Returns:
        A mapping structure
    """
    if isinstance(map_structure, Mapping):
        prop_dict = {}
        for prop_name, prop_def in map_structure.items():
            prop_type = build_or_get_type(prop_def, type_registry)
            prop_dict[prop_name] = prop_type

        type_structure = types.TypeStructure(types.StructureType.MAPPING, prop_dict)

    else:
        # A sequence

        # Requires a key type and a value type.
        assert len(map_structure) == 2

        key_type_def = map_structure[0]
        value_type_def = map_structure[1]

        key_type = build_or_get_type(key_type_def, type_registry)
        value_type = build_or_get_type(value_type_def, type_registry)

        if key_type not in (TYPE_STRING, TYPE_INTEGER):
            raise InvalidKeyTypeError(key_type)

        type_structure = types.TypeStructure(
            types.StructureType.MAPPING, [key_type, value_type]
        )

    return type_structure


def _build_list_structure(
    list_structure: _NestedTypeDefOrRef, type_registry: _TypeRegistry
) -> types.TypeStructure:
    """
    Build a TypeStructure instance from a definition of a list structure.

    Args:
        list_structure: The structure definition
        type_registry: A type registry, used to look up type references

    Returns:
        A list structure
    """
    elt_type = build_or_get_type(list_structure, type_registry)

    type_structure = types.TypeStructure(types.StructureType.LIST, elt_type)

    return type_structure


def _build_tuple_structure(
    tuple_structure: Iterable[_NestedTypeDefOrRef], type_registry: _TypeRegistry
) -> types.TypeStructure:
    """
    Build a TypeStructure instance from a definition of a tuple structure.

    Args:
        tuple_structure: The structure definition
        type_registry: A type registry, used to look up type references

    Returns:
        A tuple structure
    """
    elt_types = []
    for elt_structure_def in tuple_structure:
        elt_type = build_or_get_type(elt_structure_def, type_registry)
        elt_types.append(elt_type)

    type_structure = types.TypeStructure(types.StructureType.TUPLE, elt_types)

    return type_structure


def _build_structure(
    type_def: _TypeDefinition, type_registry: _TypeRegistry
) -> Optional[types.TypeStructure]:
    """
    Build a TypeStructure instance from a structure definition within a
    type definition.

    Args:
        type_def: A type definition
        type_registry: A type registry, used to look up type references

    Returns:
        The structure instance, or None if the type definition did not define
        any structure.
    """
    structures = {
        structure_type: type_def[structure_type.name.lower()]
        for structure_type in types.StructureType
        if structure_type.name.lower() in type_def
    }

    if len(structures) > 1:
        raise TooManyTypeStructuresError(list(structures))

    structure_type, structure_def = next(iter(structures.items()), (None, None))

    # Asserts below are for mypy; they reflect data structure (e.g. YAML
    # structure), which is something which would be enforced in JSON-Schema.
    # This code processes and is dependent upon proper data structure.
    if structure_type is types.StructureType.LIST:  # noqa: E721
        assert isinstance(structure_def, (Mapping, str))
        structure = _build_list_structure(structure_def, type_registry)
    elif structure_type is types.StructureType.MAPPING:  # noqa: E721
        assert isinstance(structure_def, (Mapping, Sequence))
        structure = _build_mapping_structure(structure_def, type_registry)
    elif structure_type is types.StructureType.TUPLE:  # noqa: E721
        assert isinstance(structure_def, Iterable)
        structure = _build_tuple_structure(structure_def, type_registry)
    else:
        structure = None

    return structure


def _build_member_types(
    member_type_defs: Iterable[_NestedTypeDefOrRef], type_registry: _TypeRegistry
) -> list[types.Type]:
    """
    Create the member types described by a union type definition.

    Args:
        member_type_defs: The member type definitions of the union
        type_registry: A type registry, used to look up type references

    Returns:
        A list of Type instances which are the member types
    """
    member_types = []

    for member_type_def in member_type_defs:
        member_type = build_or_get_type(member_type_def, type_registry)

        member_types.append(member_type)

    return member_types


def build_or_get_type(
    type_def: _NestedTypeDefOrRef, type_registry: _TypeRegistry
) -> types.Type:
    """
    Useful in nested contexts where either a nested anonymous type definition
    or the name of a registered type is allowed.  This function will return the
    registered type if type_def is just a name (string), otherwise it will
    treat type_def as a spec for an anonymous type, build that, and return it.

    Args:
        type_def: A type name or definition
        type_registry: The type registry as has been built so far

    Returns:
        A Type instance
    """
    if isinstance(type_def, str):
        type_ = type_registry[type_def]

    else:
        type_ = build_type(None, type_def, type_registry)

    return type_


def build_type(
    type_name: Optional[str],
    type_def: Optional[_TypeDefinition],
    type_registry: _TypeRegistry,
) -> types.Type:
    """
    Create a Type instance from a name and a type definition.

    Args:
        type_name: The type name; may be None if creating an anonymous type
        type_def: The type definition; may be None if creating a simple type
        type_registry: A type registry, used to look up type references

    Returns:
        A Type instance
    """
    if type_def is None:
        # Simple type
        member_type_defs = super_type_name = structure = None

    else:
        # Non-simple type
        member_type_defs = type_def.get("union")
        super_type_name = type_def.get("is_a")
        structure = _build_structure(type_def, type_registry)

    if super_type_name:
        super_type = type_registry[super_type_name]
    else:
        super_type = None

    if member_type_defs:
        member_types = _build_member_types(member_type_defs, type_registry)
    else:
        member_types = None

    # Sanity checks
    if super_type and (structure or member_types):
        raise DioptraTypeError("Structure/union types can't have a super-type")

    if structure and member_types:
        raise DioptraTypeError("A type may not be both structured and union")

    type_: types.Type
    if structure:
        type_ = types.StructuredType(structure, type_name)

    elif member_types:
        type_ = types.UnionType(member_types, type_name)

    else:  # else, a simple type
        if super_type and not isinstance(super_type, types.SimpleType):
            raise NonSimpleSuperTypeError(super_type_name)

        # Here, super_type must either be null or an instance of SimpleType
        # (the negation of the above if condition).  I.e. it satisfies
        # Optional[SimpleType].  But mypy can't seem to grok this.  And I
        # don't think there's a simple type guard you can use.  So just cast.
        super_type = cast(Optional[types.SimpleType], super_type)

        if type_name is None:
            raise AnonymousSimpleTypeError()

        type_ = types.SimpleType(type_name, super_type)

    return type_


def get_dependency_types(  # noqa: C901
    type_def: Optional[Union[_TypeDefinition, str]]
) -> Iterator[str]:
    """
    Search the given type definition and generate all references to other
    types found within.

    Args:
        type_def: A type definition

    Yields:
        Dependency type names
    """
    if isinstance(type_def, str):
        yield type_def

    elif type_def is not None:
        # Check structures
        for struct_type in types.StructureType:
            struct_def = type_def.get(struct_type.name.lower())
            if struct_def:
                break
        else:
            struct_def = None

        if struct_def:
            if struct_type is types.StructureType.MAPPING:  # noqa: E721
                if isinstance(struct_def, Mapping):
                    for prop_type in struct_def.values():
                        yield from get_dependency_types(prop_type)

                else:
                    # [key type, value type] list
                    yield from get_dependency_types(struct_def[0])
                    yield from get_dependency_types(struct_def[1])

            elif struct_type is types.StructureType.LIST:  # noqa: E721
                yield from get_dependency_types(struct_def)

            else:
                # Must be a tuple structure
                for elt in struct_def:
                    yield from get_dependency_types(elt)

        # Check unions
        union = type_def.get("union")
        if union:
            for elt in union:
                yield from get_dependency_types(elt)

        # Check supertype
        super_type = type_def.get("is_a")
        if super_type:
            yield super_type


def get_sorted_types(type_defs: Mapping[str, _TypeDefinition]) -> list[str]:
    """
    Find a topological sorted list of type names for the given type
    definitions.

    Args:
        type_defs: Type definitions, as a mapping from type name to type
            definition.

    Returns:
        A list of type names
    """
    topo_sorter: graphlib.TopologicalSorter = graphlib.TopologicalSorter()

    for type_name, type_def in type_defs.items():
        topo_sorter.add(type_name)

        for dep_type in get_dependency_types(type_def):
            if dep_type not in type_defs and dep_type not in BUILTIN_TYPES:
                raise TypeNotFoundError(dep_type, context_type_name=type_name)

            topo_sorter.add(type_name, dep_type)

    try:
        sorted_types = list(topo_sorter.static_order())
    except graphlib.CycleError as e:
        raise TypeReferenceCycleError(e.args[1]) from e

    return sorted_types


def build_type_registry(
    type_defs: Mapping[str, _TypeDefinition]
) -> Mapping[str, types.Type]:
    """
    Create a type registry from a set of type definitions.

    Args:
        type_defs: The type definitions, a mapping type name to type definition

    Returns:
        A type registry, as a mapping from type name to Type instance.  The
        mapping will also include builtin types which are not explicitly
        defined in the given type definitions, so that the registry includes
        all known types.
    """
    # start with our "builtin" types.  Need a cast because the inferred type
    # of BUILTIN_TYPES is dict[str, SimpleType] since I just have simple types
    # in it for now.  So it's not technically wrong... but I intend to do
    # whatever I want with my copy, including putting other kinds of types into
    # it.
    type_registry = cast(MutableMapping[str, types.Type], BUILTIN_TYPES.copy())

    sorted_type_names = get_sorted_types(type_defs)

    for type_name in sorted_type_names:
        # The topo sorter will add all values to the sorted list regardless of
        # whether they actually label a node (e.g. if a value *only* shows up
        # in a list of prerequisites).  So it is possible to have values in the
        # topo sorted list which are not keys in the type_defs mapping.  These
        # correspond to references to built-in types (not errors) or undefined
        # types (errors).

        if type_name in BUILTIN_TYPES:
            if type_name in type_defs:
                raise BuiltinTypeRedefinitionError(type_name)

        else:
            try:
                type_ = build_type(type_name, type_defs[type_name], type_registry)
            except DioptraTypeError as e:
                if not e.context_type_name:
                    e.context_type_name = type_name
                raise

            type_registry[type_name] = type_

    return type_registry
