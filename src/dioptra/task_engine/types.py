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
Define classes related to types.
"""

import enum
from collections.abc import Iterable, Mapping, Sequence, Set
from typing import Any, Optional, Union

# This creates a circular import.  The exception module imports this module
# because it needs these type classes as annotations.  I would like exception
# instances related to types to be able to store the relevant type objects.
# This module needs to raise exceptions, so it has to import the exceptions
# module.  So each module needs to import the other.  So we need to be careful
# how each module uses the other.  A "from X import Y" style import will not
# work here.
import dioptra.sdk.exceptions.task_engine


class StructureType(enum.Enum):
    """
    Define type structures, for structured types.
    """

    MAPPING = enum.auto()
    LIST = enum.auto()
    TUPLE = enum.auto()


def _make_iterable_hashable(iterable: Iterable[Any]) -> tuple[Any, ...]:
    """
    Make an arbitrary iterable into a hashable value.  The hash will be
    sensitive to value order within the iterable.

    Args:
        iterable: The iterable to convert

    Returns:
        A tuple of hashable values which represents the given iterable
    """

    hashable = tuple(_make_hashable(elt) for elt in iterable)

    return hashable


def _make_mapping_hashable(mapping: Mapping[Any, Any]) -> frozenset[Any]:
    """
    Make an arbitrary mapping into a hashable value.  The hash will be
    insensitive to any inherent entry ordering within the mapping.

    Args:
        mapping: The mapping to convert

    Returns:
        A frozenset of 2-tuples, which represents the given mapping
    """
    # assume keys are hashable (probably strings).  Using a frozenset ensures
    # the hash function is agnostic to an iteration order.  We want it to
    # depend only on the keys and values.  That's also how dict equality works.
    hashable = frozenset((key, _make_hashable(value)) for key, value in mapping.items())

    return hashable


def _make_hashable(value: Any) -> Any:
    """
    Make a hashable value from the given value.  This will transform the value
    to something else, which is representative of the original but hashable,
    if the value isn't already hashable.

    Args:
        value: The value to convert

    Returns:
        A hashable value
    """
    result: Any
    if isinstance(value, set):
        result = frozenset(value)  # just in case?
    elif isinstance(value, Mapping):
        result = _make_mapping_hashable(value)
    elif isinstance(value, Iterable) and not isinstance(value, str):
        result = _make_iterable_hashable(value)
    else:
        # else, assume hashability.
        result = value

    return result


class TypeStructure:
    """
    Instances represent the required structure of a structured type.
    """

    def __init__(
        self,
        struct_type: StructureType,
        struct_def: Union["Type", Mapping[str, "Type"], Sequence["Type"]],
    ) -> None:
        """
        Initialize this instance.

        Args:
            struct_type: A StructureType enum value which represents the
                structure type
            struct_def: The structure definition, which must be compatible with
                the chosen structure type.  This is only lightly validated at
                runtime, but must be a Type instance for lists, a sequence of
                Type instances for tuples and key/value type mappings (sequence
                length must be 2 for the latter), and a string->Type mapping
                for enumerated mapping structures.
        """

        self.__struct_type = struct_type
        self.__struct_def = struct_def

        self.__check_structure_agrees_with_type()

    @property
    def struct_type(self) -> StructureType:
        """
        The type of structure
        """
        return self.__struct_type

    @property
    def struct_def(self) -> Union["Type", Mapping[str, "Type"], Sequence["Type"]]:
        """
        The structure definition
        """
        return self.__struct_def

    def __check_structure_agrees_with_type(self) -> None:
        """
        Do a light sanity check of the structure definition given against
        the structure type.
        """
        if self.struct_type is StructureType.MAPPING and not isinstance(
            self.struct_def, (Mapping, Sequence)
        ):
            raise dioptra.sdk.exceptions.task_engine.InvalidTypeStructureDefinitionError(  # noqa: B950
                "For mapping type structures, the definition must be"
                " either a mapping (e.g. a dict) from property names to types,"
                " or a 2-element list containing a key type followed by a value"
                " type"
            )

        elif self.struct_type is StructureType.LIST and not isinstance(
            self.struct_def, Type
        ):
            raise dioptra.sdk.exceptions.task_engine.InvalidTypeStructureDefinitionError(  # noqa: B950
                "For a list type structure, the definition must be a type"
            )

        elif self.struct_type is StructureType.TUPLE and not isinstance(
            self.struct_def, Sequence
        ):
            raise dioptra.sdk.exceptions.task_engine.InvalidTypeStructureDefinitionError(  # noqa: B950
                "For a tuple type structure, the definition must be a sequence"
                " of types"
            )

    def __eq__(self, other: Any) -> bool:
        """
        Check this type for equality against another.

        Args:
            other: The other value

        Returns:
            True if equal, False if not
        """

        result = False
        if self is other:
            result = True
        elif isinstance(other, TypeStructure):
            result = (
                self.struct_type is other.struct_type
                and self.struct_def == other.struct_def
            )
        # The above "==" check should automatically recurse inside structures.

        return result

    def __hash__(self) -> int:
        """
        Compute a hash value from this instance.

        Returns:
            The hash value
        """
        hashable_struct = _make_hashable(self.struct_def)

        return hash((self.struct_type, hashable_struct))

    def __repr__(self) -> str:
        """
        Create a readable repr string from this instance.

        Returns:
            The repr string
        """
        return "TypeStructure({!s}, {!r})".format(self.struct_type, self.struct_def)

    def __str__(self) -> str:
        """
        Create a readable string representation of this instance.

        Returns:
            The string representation
        """
        if self.struct_type is StructureType.MAPPING:
            if isinstance(self.struct_def, Mapping):
                # Enumerated key mapping structure
                struct_def_str = (
                    "{"
                    + ", ".join(
                        repr(k) + ": " + str(v) for k, v in self.struct_def.items()
                    )
                    + "}"
                )

            else:
                # Key type + value type mapping structure
                assert isinstance(self.struct_def, Sequence)  # for mypy
                struct_def_str = ", ".join(
                    str(elt_type) for elt_type in self.struct_def
                )

        elif self.struct_type is StructureType.LIST:
            struct_def_str = str(self.struct_def)

        else:  # tuple structure
            assert isinstance(self.struct_def, Sequence)  # for mypy
            struct_def_str = ", ".join(str(elt_type) for elt_type in self.struct_def)

        return self.struct_type.name + "[" + struct_def_str + "]"


class Type:
    """
    Immutable base class of all types.
    """

    def __init__(self, name: Optional[str] = None) -> None:
        """
        Initialize this type.

        Args:
            name: The type name
        """
        self.__name = name

    @property
    def name(self) -> Optional[str]:
        """
        The name of this type
        """
        return self.__name

    def __hash__(self) -> int:
        """
        Abstract __hash__ implementation; subclasses must override.
        """
        # Required so we can put types in sets
        raise NotImplementedError()

    def __eq__(self, other: Any) -> bool:
        """
        Abstract __eq__ implementation; subclasses must override.
        """
        raise NotImplementedError()


class SimpleType(Type):
    """
    Instances represent "simple" types: those which just have names.
    """

    def __init__(self, name: str, super_type: Optional["SimpleType"] = None) -> None:
        """
        Initialize this simple type.

        Args:
            name: The name of the type
            super_type: The super-type
        """

        if name is None:
            raise ValueError("Simple types must have a name")

        super().__init__(name)

        self.__super_type = super_type

    @property
    def name(self) -> str:
        """
        Overrides superclass "name" property to have "str" return type.  Simple
        types always have names (there is a check in the constructor), but the
        superclass property has type Optional[str] since other kinds of types
        may be anonymous (have no name).  I think it's easier to have this
        override in place, than to have to add asserts for mypy every single
        time I refer to the name of a simple type in a non-optional "str"
        context.

        Returns:
            The name of this type
        """
        name = super().name
        # Required for mypy: simple types always have names.
        assert name is not None
        return name

    @property
    def super_type(self) -> Optional["SimpleType"]:
        """
        The super-type
        """
        return self.__super_type

    def is_subtype_of(self, other: Any) -> bool:
        """
        Determine whether this type is a subtype of the other

        Args:
            other: A type

        Returns:
            True if self is a subtype of other; False if not
        """
        result = False
        type_ = self.super_type
        while type_ is not None:
            if type_ == other:
                result = True
                break
            type_ = type_.super_type

        return result

    def __eq__(self, other: Any) -> bool:
        """
        Determine whether self is equal to other.

        Args:
            other: Another value to compare to self

        Returns:
            True if self is equal to other; False if not
        """
        # If names equal, we treat the types as equal.  It is not legal to have
        # two types with the same name but which are different in some other
        # respect.  Treat the names as representative of everything else.
        # Simple types must have names; they can't be anonymous.
        result = False
        if self is other:
            result = True
        elif isinstance(other, SimpleType):
            result = self.name == other.name

        return result

    def __hash__(self) -> int:
        """
        Compute a hash value for this type

        Returns:
            The hash value
        """
        # See __eq__: name is uniquely representative
        return hash(self.name)

    def __repr__(self) -> str:
        """
        Create a readable repr string for this type.

        Returns:
            The repr string
        """
        return "SimpleType(name={!r}, super_type={!r})".format(
            self.name, self.super_type
        )

    def __str__(self) -> str:
        """
        Create a readable string representation of this type.

        Returns:
            The string representation
        """
        # Just name, to decrease verbosity
        return self.name


class StructuredType(Type):
    """
    Instances represent "structured" types, i.e. those with defined internal
    structure.
    """

    def __init__(self, structure: TypeStructure, name: Optional[str] = None) -> None:
        """
        Initialize this type.

        Args:
            structure: The structure of this type
            name: The name of this type
        """
        super().__init__(name)

        if structure is None:
            raise ValueError("Structured types must have a structure")

        self.__structure = structure

    @property
    def structure(self) -> TypeStructure:
        """
        The structure of this type
        """
        return self.__structure

    def __eq__(self, other: Any) -> bool:
        """
        Determine whether self is equal to other.

        Args:
            other: Another value to compare to self

        Returns:
            True if self is equal to other; False if not
        """
        result = False
        if self is other:
            result = True
        elif isinstance(other, StructuredType):
            result = self.name == other.name

            if result and self.name is None:
                result = self.structure == other.structure

            # else: if names equal and not None, we treat the types as equal.
            # It is not legal to have two types with the same name but which are
            # different in some other respect.  Treat the names as
            # representative of everything else.  If we have names, there is no
            # need to check anything else.

        return result

    def __hash__(self) -> int:
        """
        Compute a hash value for this type

        Returns:
            The hash value
        """
        if self.name is not None:
            result = hash(self.name)
        else:
            # anonymous: defined by its structure
            result = hash(self.structure)

        return result

    def __repr__(self) -> str:
        """
        Create a readable repr string for this type.

        Returns:
            The repr string
        """
        return "StructuredType(structure={!r}, name={!r})".format(
            self.structure, self.name
        )

    def __str__(self) -> str:
        """
        Create a readable string representation of this type.

        Returns:
            The string representation
        """
        s = "{}: {}".format(self.name or "<anon>", str(self.structure))

        return s


class UnionType(Type):
    """
    Instances represent union types.
    """

    def __init__(self, member_types: Iterable[Type], name=None) -> None:
        """
        Initialize this type.

        Args:
            member_types: The member types of the union
            name: The name of this type
        """
        super().__init__(name)

        # Use set to dedupe and obtain order-agnosticism
        self.__member_types = frozenset(member_types)

    @property
    def member_types(self) -> Set[Type]:
        """
        The member types of the union.
        """
        return self.__member_types

    def __eq__(self, other: Any) -> bool:
        """
        Determine whether self is equal to other.

        Args:
            other: Another value to compare to self

        Returns:
            True if self is equal to other; False if not
        """
        result = False
        if self is other:
            result = True
        elif isinstance(other, UnionType):
            result = self.name == other.name

            if result and self.name is None:
                result = self.member_types == other.member_types

            # else: if names equal and not None, we treat the types as equal.
            # It is not legal to have two types with the same name but which are
            # different in some other respect.  Treat the names as
            # representative of everything else.  If we have names, there is no
            # need to check anything else.

        return result

    def __hash__(self) -> int:
        """
        Compute a hash value for this type

        Returns:
            The hash value
        """
        if self.name is not None:
            result = hash(self.name)
        else:
            # anonymous: defined by its members
            result = hash(self.member_types)

        return result

    def __repr__(self) -> str:
        """
        Create a readable repr string for this type.

        Returns:
            The repr string
        """
        # I like the bracketed list look more than frozenset(...).
        members_list_repr = "[" + ", ".join(repr(m) for m in self.member_types) + "]"
        return "UnionType(member_types={}, name={!r})".format(
            members_list_repr, self.name
        )

    def __str__(self) -> str:
        """
        Create a readable string representation of this type.

        Returns:
            The string representation
        """
        s = "{}: UNION[{}]".format(
            self.name or "<anon>", ", ".join(str(t) for t in self.member_types)
        )

        return s
