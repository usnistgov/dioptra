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
Implement static type validation for a declarative experiment description.
"""

import functools
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Optional

from dioptra.sdk.exceptions.task_engine import ValidationLimitError
from dioptra.task_engine import type_registry, types, util
from dioptra.task_engine.issues import (
    IssueSeverity,
    IssueType,
    ValidationIssue,
    ValidationLimitIssue,
)
from dioptra.task_engine.type_validation_state import (
    Comparison,
    TypeValidationLimits,
    TypeValidationState,
)

# Type aliases for type annotations
_TypeMap = Mapping[str, types.Type]
# Map from a name to a definition of something.  Applicable to types, tasks,
# parameters, graph steps.
_DefMap = Mapping[str, Any]


def _get_reference_type(
    reference: str,
    type_reg: _TypeMap,
    global_parameter_types: _TypeMap,
    graph: _DefMap,
    tasks: _DefMap,
    artifact_inputs: _DefMap,
) -> types.Type:
    """
    Given a reference, look up its type.

    Args:
        reference: A reference, without the leading "$"
        type_reg: A type registry as a mapping from type name to Type instance
        global_parameter_types: A mapping from global parameter name to
            Type instance, giving the types of all global parameters
        graph: A task graph, mapping step names to step definitions
        tasks: Task definitions, mapping task short name to task definition

    Returns:
        A type
    """

    if "." in reference:
        ref_name, ref_output_name = reference.split(".", 1)

    else:
        ref_name = reference
        ref_output_name = None

    # Lots of correctness assumptions inherent below.  E.g. that other
    # validation has previously occurred, to catch things like bad references.
    if ref_output_name is None and ref_name in global_parameter_types:
        type_ = global_parameter_types[ref_name]

    elif ref_name in artifact_inputs:
        artifact_outputs = artifact_inputs[ref_name]
        if not isinstance(artifact_outputs, list):
            artifact_outputs = [artifact_outputs]

        output_type_name = None
        if ref_output_name is None:
            output_def = artifact_outputs[0]
            output_type_name = next(iter(output_def.values()))
        else:
            for output_def in artifact_outputs:
                this_output_name, output_type_name = next(iter(output_def.items()))
                if this_output_name == ref_output_name:
                    break

        # Assume references have already been validated, so we will always
        # find an output which matches the reference.
        assert output_type_name
        type_ = type_reg[output_type_name]

    else:
        step_def = graph[ref_name]
        task_short_name = util.step_get_plugin_short_name(step_def)

        # Assume well-formed step definition (see the comment about
        # correctness assumptions above... but we still have to satisfy mypy)
        assert task_short_name is not None

        task_def = tasks[task_short_name]
        task_outputs = task_def.get("outputs", [])

        if not isinstance(task_outputs, list):
            task_outputs = [task_outputs]

        output_type_name = None
        if ref_output_name is None:
            output_def = task_outputs[0]
            output_type_name = next(iter(output_def.values()))
        else:
            for output_def in task_outputs:
                this_output_name, output_type_name = next(iter(output_def.items()))
                if this_output_name == ref_output_name:
                    break

        # Assume references have already been validated, so we will always
        # find an output which matches the reference.
        assert output_type_name
        type_ = type_reg[output_type_name]

    return type_


def _is_subtype(
    type_: types.SimpleType, other: types.SimpleType, state: TypeValidationState
) -> bool:
    """Check ancestry, counting each supertype visited against the work limit."""
    current = type_.super_type
    while current is not None:
        state.charge()
        if current.name == other.name:
            return True
        current = current.super_type
    return False


def _find_common_base_of_two_types(
    type1: types.Type, type2: types.Type, state: TypeValidationState
) -> types.Type:
    """
    Find the most specific common base type between the pair of types given.
    Will return the "any" type if nothing more specific is found.

    Args:
        type1: A Type instance
        type2: A Type instance
        state: State shared by the current validation.

    Returns:
        A Type instance
    """
    common_base: Optional[types.Type]

    if isinstance(type1, types.SimpleType) and isinstance(type2, types.SimpleType):
        if type1 == type2:
            common_base = type1
        elif _is_subtype(type1, type2, state):
            common_base = type2
        elif _is_subtype(type2, type1, state):
            common_base = type1
        else:
            # Try to find a base of type1 which is also a base of type2.
            common_base = type1.super_type
            while common_base is not None:
                if _is_subtype(type2, common_base, state):
                    break
                common_base = common_base.super_type
            else:
                # Can't find a common base, so use any.
                common_base = type_registry.TYPE_ANY

    else:
        common_base = type_registry.TYPE_ANY

    return common_base


def _find_common_base_type(
    types_: Iterable[types.Type], state: TypeValidationState
) -> types.Type:
    """
    Find the most specific common base type among all of the given types.  Will
    return the "any" type if nothing more specific is found.

    Args:
        types_: An iterable of Type instances
        state: State shared by the current validation.

    Returns:
        A Type instance
    """
    try:
        common_base = functools.reduce(
            lambda left, right: _find_common_base_of_two_types(left, right, state),
            types_,
        )
    except TypeError as e:
        raise ValueError("_find_common_base_type() requires at least one type") from e

    return common_base


def _infer_type_from_mapping(
    mapping: Mapping,
    type_reg: Optional[_TypeMap] = None,
    global_parameter_types: Optional[_TypeMap] = None,
    graph: Optional[_DefMap] = None,
    tasks: Optional[_DefMap] = None,
    artifact_inputs: Optional[_DefMap] = None,
    *,
    state: TypeValidationState,
) -> types.Type:
    """
    Infer the type of the given Mapping value.  This always produces a mapping
    type.  If the latter four parameters are non-None, reference resolution is
    enabled.  That means if the value contains strings which look like a
    reference, they are looked up and resolved to types.  If reference
    resolution is disabled, the string type will be inferred for all string
    values, no matter what they look like.

    Args:
        mapping: The mapping value to infer a type for
        state: State shared by the current validation.
        type_reg: A type registry as a mapping from type name to Type instance
        global_parameter_types: A mapping from global parameter name to
            Type instance, giving the types of all global parameters
        graph: A task graph, mapping step names to step definitions
        tasks: Task definitions, mapping task short name to task definition

    Returns:
        The value type
    """
    type_: types.Type

    if mapping:
        key_types = (
            # disable reference resolution here
            _infer_type(key, state=state)
            for key in mapping
        )

        key_base_type = _find_common_base_type(key_types, state=state)

        if key_base_type is type_registry.TYPE_STRING:
            # If keys are strings, infer an enumerated mapping type
            prop_types = {
                prop_name: _infer_type(
                    prop_value,
                    type_reg,
                    global_parameter_types,
                    graph,
                    tasks,
                    artifact_inputs,
                    state=state,
                )
                for prop_name, prop_value in mapping.items()
            }

            type_ = types.StructuredType(
                types.TypeStructure(types.StructureType.MAPPING, prop_types)
            )

        elif key_base_type is type_registry.TYPE_INTEGER:
            # Integer-keyed keytype/valuetype style mappings are also
            # permitted.  Need to come up with a single type from potentially
            # multiple different property value types.
            value_types = {
                _infer_type(
                    v,
                    type_reg,
                    global_parameter_types,
                    graph,
                    tasks,
                    artifact_inputs,
                    state=state,
                )
                for v in mapping.values()
            }

            if len(value_types) == 1:
                value_type = next(iter(value_types))
            else:
                value_type = types.UnionType(value_types)

            type_ = types.StructuredType(
                types.TypeStructure(
                    types.StructureType.MAPPING, [key_base_type, value_type]
                )
            )

        else:
            # Else, there is no mapping type in the type system which
            # supports the combination of key and value types present in
            # the mapping.  So we must infer any.
            type_ = type_registry.TYPE_ANY

    else:
        # If an empty mapping, mapping[{}] is inferred (i.e. enumerated
        # property mapping with no properties).
        type_ = types.StructuredType(
            types.TypeStructure(types.StructureType.MAPPING, {})
        )

    return type_


def _infer_type_from_iterable(
    iterable: Iterable,
    type_reg: Optional[_TypeMap] = None,
    global_parameter_types: Optional[_TypeMap] = None,
    graph: Optional[_DefMap] = None,
    tasks: Optional[_DefMap] = None,
    artifact_inputs: Optional[_DefMap] = None,
    *,
    state: TypeValidationState,
) -> types.Type:
    """
    Infer the type of the given iterable value.  This always produces a tuple
    type.  If the latter four parameters are non-None, reference resolution is
    enabled.  That means if the value contains strings which look like a
    reference, they are looked up and resolved to types.  If reference
    resolution is disabled, the string type will be inferred for all string
    values, no matter what they look like.

    Args:
        iterable: The iterable value to infer a type for
        state: State shared by the current validation.
        type_reg: A type registry as a mapping from type name to Type instance
        global_parameter_types: A mapping from global parameter name to
            Type instance, giving the types of all global parameters
        graph: A task graph, mapping step names to step definitions
        tasks: Task definitions, mapping task short name to task definition

    Returns:
        The value type
    """
    # Infer all element types
    elt_types = [
        _infer_type(
            elt,
            type_reg,
            global_parameter_types,
            graph,
            tasks,
            artifact_inputs,
            state=state,
        )
        for elt in iterable
    ]

    type_ = types.StructuredType(
        types.TypeStructure(types.StructureType.TUPLE, elt_types)
    )

    return type_


def _infer_type(
    value: Any,
    type_reg: Optional[_TypeMap] = None,
    global_parameter_types: Optional[_TypeMap] = None,
    graph: Optional[_DefMap] = None,
    tasks: Optional[_DefMap] = None,
    artifact_inputs: Optional[_DefMap] = None,
    *,
    state: TypeValidationState,
) -> types.Type:
    """
    Infer the type of the given value.  If the latter four parameters are
    non-None, reference resolution is enabled.  That means if the value is or
    contains strings which look like a reference, they are looked up and
    resolved to types.  If reference resolution is disabled, the string type
    will be inferred for all string values, no matter what they look like.

    Args:
        value: The value to infer a type for
        state: State shared by the current validation.
        type_reg: A type registry as a mapping from type name to Type instance
        global_parameter_types: A mapping from global parameter name to
            Type instance, giving the types of all global parameters
        graph: A task graph, mapping step names to step definitions
        tasks: Task definitions, mapping task short name to task definition

    Returns:
        The value type
    """
    state.charge()
    if isinstance(value, str):
        if (
            util.is_reference(value)
            and type_reg is not None
            and global_parameter_types is not None
            and graph is not None
            and tasks is not None
            and artifact_inputs is not None
        ):
            type_ = _get_reference_type(
                value[1:],
                type_reg,
                global_parameter_types,
                graph,
                tasks,
                artifact_inputs,
            )
        else:
            type_ = type_registry.TYPE_STRING

    elif isinstance(value, bool):
        type_ = type_registry.TYPE_BOOLEAN

    elif isinstance(value, int):
        type_ = type_registry.TYPE_INTEGER

    elif isinstance(value, float):
        type_ = type_registry.TYPE_NUMBER

    elif value is None:
        type_ = type_registry.TYPE_NULL

    elif isinstance(value, Mapping):
        type_ = _infer_type_from_mapping(
            value,
            type_reg,
            global_parameter_types,
            graph,
            tasks,
            artifact_inputs,
            state=state,
        )

    elif util.is_iterable(value):
        type_ = _infer_type_from_iterable(
            value,
            type_reg,
            global_parameter_types,
            graph,
            tasks,
            artifact_inputs,
            state=state,
        )

    else:
        # If we can't get any more specific, infer the "any" type
        type_ = type_registry.TYPE_ANY

    return type_


def _mapping_structures_compatible(
    invoc_map_struct: types.TypeStructure,
    task_map_struct: types.TypeStructure,
    state: TypeValidationState,
) -> bool:
    """
    Check an invocation mapping structure for compatibility with a task
    parameter mapping structure.

    Args:
        invoc_map_struct: An invocation mapping structure
        task_map_struct: A task parameter mapping structure
        state: State shared by the current validation.

    Returns:
        True if the structures are compatible; False if not
    """
    invoc_struct_def = invoc_map_struct.struct_def
    # Whether the mapping structure is of the enumerated property style or the
    # keytype/valuetype style.
    invoc_is_enumerated = isinstance(invoc_struct_def, Mapping)

    task_struct_def = task_map_struct.struct_def
    task_is_enumerated = isinstance(task_struct_def, Mapping)

    if invoc_is_enumerated and task_is_enumerated:
        # Mappings must have the same properties, and property types must
        # be compatible

        # This is redundant because this is what invoc_is_enumerated and
        # task_is_enumerated (being True) means.  The code is more
        # understandable with those variables.  I want readers to not only
        # understand the Python types but the ramifications regarding the type
        # system implemented here: that both the invocation arg and task
        # parameter types are *enumerated* mappings in this case.  But mypy
        # can't see that.
        assert isinstance(invoc_struct_def, Mapping)
        assert isinstance(task_struct_def, Mapping)

        result = len(invoc_struct_def) == len(task_struct_def)

        if result:
            for invoc_prop_name, invoc_prop_type in state.members(
                invoc_struct_def.items()
            ):
                task_prop_type = task_struct_def.get(invoc_prop_name)

                if task_prop_type:
                    result = _types_compatible(
                        invoc_prop_type, task_prop_type, state=state
                    )
                else:
                    result = False

                if not result:
                    break

    elif invoc_is_enumerated and not task_is_enumerated:
        # Task key type must be string, and all invocation property types
        # must be compatible with the task value type

        # Redundant, for mypy
        assert isinstance(invoc_struct_def, Mapping)
        assert isinstance(task_struct_def, Sequence)

        task_key_type, task_value_type = task_struct_def

        result = task_key_type is type_registry.TYPE_STRING

        if result:
            result = all(
                _types_compatible(invoc_prop_type, task_value_type, state=state)
                for invoc_prop_type in state.members(invoc_struct_def.values())
            )

    elif not invoc_is_enumerated and task_is_enumerated:
        # Can't pass a keytype/valuetype mapping to an enumerated mapping.

        result = False

    else:
        # Neither mapping structure is enumerated.  Key types and value
        # types must be compatible.

        # Redundant, for mypy
        assert isinstance(invoc_struct_def, Sequence)
        assert isinstance(task_struct_def, Sequence)

        invoc_key_type, invoc_value_type = invoc_struct_def
        task_key_type, task_value_type = task_struct_def

        result = all(
            _types_compatible(argument, parameter, state=state)
            for argument, parameter in state.members(
                ((invoc_key_type, task_key_type), (invoc_value_type, task_value_type))
            )
        )

    return result


def _tuple_structures_compatible(
    invoc_tuple_struct: types.TypeStructure,
    task_tuple_struct: types.TypeStructure,
    state: TypeValidationState,
) -> bool:
    """
    Check an invocation tuple structure for compatibility with a task parameter
    tuple structure.

    Args:
        invoc_tuple_struct: An invocation tuple structure
        task_tuple_struct: A task parameter tuple structure
        state: State shared by the current validation.

    Returns:
        True if the structures are compatible; False if not
    """
    invoc_struct_def = invoc_tuple_struct.struct_def
    task_struct_def = task_tuple_struct.struct_def

    # For mypy: tuple structures are sequences (the element types)
    assert isinstance(invoc_struct_def, Sequence)
    assert isinstance(task_struct_def, Sequence)

    result = len(invoc_struct_def) == len(task_struct_def)

    if result:
        for invoc_elt_type, task_elt_type in state.members(
            zip(invoc_struct_def, task_struct_def)
        ):
            if not _types_compatible(invoc_elt_type, task_elt_type, state=state):
                result = False
                break

    return result


def _types_compatible_structured(
    invocation_arg_type: types.StructuredType,
    task_param_type: types.StructuredType,
    state: TypeValidationState,
) -> bool:
    """
    Check an invocation argument type for compatibility with a corresponding
    task parameter type, where both are structured types.

    Args:
        invocation_arg_type: An invocation argument type
        task_param_type: A task parameter argument type
        state: State shared by the current validation.

    Returns:
        True if the types are compatible; False if not
    """
    # Special tuple->list cross-type compatibility check.  This is necessary
    # because we will infer a tuple type from a list value, which needs to be
    # able to be compatible with a list type.  Compatibility could be due
    # to inheritance (e.g. tuple[int, number] needs to be compatible with
    # list[number]).
    if (
        invocation_arg_type.structure.struct_type is types.StructureType.TUPLE  # noqa: E721
        and task_param_type.structure.struct_type is types.StructureType.LIST
    ):
        tuple_elt_types = invocation_arg_type.structure.struct_def
        list_elt_type = task_param_type.structure.struct_def

        # Redundant, for mypy.
        assert isinstance(tuple_elt_types, Sequence)
        assert isinstance(list_elt_type, types.Type)

        result = all(
            _types_compatible(tuple_elt_type, list_elt_type, state=state)
            for tuple_elt_type in state.members(tuple_elt_types)
        )

    elif (
        invocation_arg_type.structure.struct_type
        is not task_param_type.structure.struct_type
    ):
        # Structure mismatch
        result = False

    # Structure types are the same; must dig into their components and
    # compare
    elif (
        invocation_arg_type.structure.struct_type is types.StructureType.MAPPING  # noqa: E721
    ):
        result = _mapping_structures_compatible(
            invocation_arg_type.structure, task_param_type.structure, state=state
        )

    elif (
        invocation_arg_type.structure.struct_type is types.StructureType.LIST  # noqa: E721
    ):
        # Redundant, for mypy.
        assert isinstance(invocation_arg_type.structure.struct_def, types.Type)
        assert isinstance(task_param_type.structure.struct_def, types.Type)

        state.charge()
        result = _types_compatible(
            invocation_arg_type.structure.struct_def,
            task_param_type.structure.struct_def,
            state=state,
        )

    else:
        # Must be tuples
        result = _tuple_structures_compatible(
            invocation_arg_type.structure, task_param_type.structure, state=state
        )

    return result


def _types_compatible(
    invocation_arg_type: types.Type,
    task_param_type: types.Type,
    state: TypeValidationState,
) -> bool:
    """
    Check an invocation argument type for compatibility with a corresponding
    task parameter type.

    Args:
        invocation_arg_type: An invocation argument type
        task_param_type: A task parameter argument type
        state: State shared by the current validation.

    Returns:
        True if the types are compatible; False if not
    """
    state.charge()
    key = (id(invocation_arg_type), id(task_param_type))
    entry = state.comparisons.get(key)
    if entry is not None:
        if entry.result is None:
            state.fail("recursive comparison")
        return entry.result
    if len(state.comparisons) >= state.limits.cache_entries:
        state.fail("comparison cache")
    if state.depth >= state.limits.comparison_depth:
        state.fail("comparison nesting")
    entry = Comparison(invocation_arg_type, task_param_type)
    state.comparisons[key] = entry
    state.depth += 1
    try:
        entry.result = _evaluate_compatibility(
            invocation_arg_type, task_param_type, state
        )
        return entry.result
    except Exception:
        # Retain pending state and prevent reuse after any aborted evaluation.
        state.exhausted = True
        raise
    finally:
        state.depth -= 1


def _evaluate_compatibility(
    invocation_arg_type: types.Type,
    task_param_type: types.Type,
    state: TypeValidationState,
) -> bool:
    """Evaluate one new directed pair using the existing compatibility rules."""
    if task_param_type is type_registry.TYPE_ANY:
        # everything is compatible with "any"
        result = True

    elif invocation_arg_type is task_param_type or (
        type(invocation_arg_type) is type(task_param_type)
        and invocation_arg_type.name is not None
        and invocation_arg_type.name == task_param_type.name
    ):
        # Simple special case which bypasses the complexity below: if types
        # are the same, they are automatically compatible.

        result = True

    # Union cases

    elif isinstance(invocation_arg_type, types.UnionType):
        # Treat invocation union like an "and" over all union members:
        # all union members must be compatible with the task parameter type.
        result = all(
            _types_compatible(invoc_member_type, task_param_type, state=state)
            for invoc_member_type in state.members(invocation_arg_type.member_types)
        )

    elif isinstance(task_param_type, types.UnionType):
        # Due to the above "if", we know the invocation arg type is not a
        # union here.  It must be compatible with some member of the task
        # parameter union.
        result = any(
            _types_compatible(invocation_arg_type, task_param_member_type, state=state)
            for task_param_member_type in state.members(task_param_type.member_types)
        )

    # Non-union cases

    elif isinstance(invocation_arg_type, types.SimpleType) and isinstance(
        task_param_type, types.SimpleType
    ):
        # Both simple, but not the same (that was checked above).  So we can do
        # a subtype check.
        result = _is_subtype(invocation_arg_type, task_param_type, state)

    elif isinstance(invocation_arg_type, types.StructuredType) and isinstance(
        task_param_type, types.StructuredType
    ):
        if invocation_arg_type.name is not None and task_param_type.name is not None:
            # We treat differently named structured types as incompatible,
            # regardless of structural compatibility.  In this case I think we
            # should treat their semantics as different, even if their inner
            # structure aligns.  Names must be unequal here, or they would be
            # the same type, and that case was checked for already.
            result = False

        else:
            result = _types_compatible_structured(
                invocation_arg_type, task_param_type, state=state
            )

    else:
        # Simple/structured type mismatch
        result = False

    return result


def _check_invocation_parameter(
    invocation_arg_spec: Any,
    task_arg: Mapping[str, Any],
    type_reg: _TypeMap,
    global_parameter_types: _TypeMap,
    graph: _DefMap,
    tasks: _DefMap,
    artifact_inputs: _DefMap,
    state: TypeValidationState,
) -> list[ValidationIssue]:
    """
    Check the type of one task invocation parameter from a step against the
    parameter definition declared with the task.

    Args:
        invocation_arg_spec: An argument spec from a task invocation in a step
        task_arg: A task argument definition from a task definition
        state: State shared by the current validation.
        type_reg: A type registry as a mapping from type name to Type instance
        global_parameter_types: A mapping from global parameter name to Type
            instance, giving the types of all global parameters
        graph: A task graph, mapping step names to step definitions
        tasks: Task definitions, mapping task short names to task definitions

    Returns:
        A list of ValidationIssue objects; will be empty if no issues were
        found
    """
    issues = []

    _, task_param_type_name = util.input_def_get_name_type(task_arg)
    # Assume type references have already been validated
    task_param_type = type_reg[task_param_type_name]

    inferred_invocation_arg_type = _infer_type(
        invocation_arg_spec,
        type_reg,
        global_parameter_types,
        graph,
        tasks,
        artifact_inputs,
        state=state,
    )

    if not _types_compatible(
        inferred_invocation_arg_type, task_param_type, state=state
    ):
        message = state.message(
            "Inferred invocation arg type and task plugin input type are incompatible. Found ",
            state.describe(inferred_invocation_arg_type),
            "; expected ",
            state.describe(task_param_type),
        )

        issue = ValidationIssue(IssueType.TYPE, IssueSeverity.ERROR, message)
        issues.append(issue)

    return issues


def _step_check_types(
    step_def: Mapping[str, Any],
    type_reg: _TypeMap,
    global_parameter_types: _TypeMap,
    graph: _DefMap,
    tasks: _DefMap,
    artifact_inputs: _DefMap,
    state: TypeValidationState,
) -> list[ValidationIssue]:
    """
    Check the types of task invocation parameters in the given step.

    Args:
        step_def: A step definition
        state: State shared by the current validation.
        type_reg: A type registry as a mapping from type name to Type instance
        global_parameter_types: A mapping from global parameter name to Type
            instance, giving the types of all global parameters
        graph: A task graph, mapping step names to step definitions
        tasks: Task definitions, mapping task short name to task definition

    Returns:
        A list of ValidationIssue objects; will be empty if no issues were
        found
    """
    # Get info about how the task plugin is being invoked, in the given step
    (
        invocation_pos_arg_specs,
        invocation_keyword_arg_specs,
    ) = util.step_get_invocation_arg_specs(step_def)

    # For mypy: assume a step definition well-formedness check has already
    # occurred, so we know we can get invocation arguments.
    assert invocation_pos_arg_specs is not None
    assert invocation_keyword_arg_specs is not None

    # Get info about the task plugin: how it needs to be invoked
    task_plugin_short_name = util.step_get_plugin_short_name(step_def)

    # For mypy: assume a step definition well-formedness check has already
    # occurred, so we know we can get a task plugin short name.
    assert task_plugin_short_name is not None

    task_def = tasks[task_plugin_short_name]
    task_inputs_map = util.make_task_input_map(task_def)

    # Now, we can evaluate the task plugin invocation with respect to its
    # parameter type requirements.

    all_issues = []

    # Check invocation positional args
    for arg_idx, (invocation_arg_spec, task_arg) in enumerate(
        zip(
            # rely on correct task_inputs_map iteration order here
            invocation_pos_arg_specs,
            task_inputs_map.values(),
        )
    ):
        issues = _check_invocation_parameter(
            invocation_arg_spec,
            task_arg,
            type_reg,
            global_parameter_types,
            graph,
            tasks,
            artifact_inputs,
            state=state,
        )

        # Augment messages with info not known at the point where the message
        # was originally created.
        for issue in issues:
            prefix = f"in positional parameter #{arg_idx + 1}: "
            state.message(prefix)
            issue.message = prefix + issue.message

        all_issues.extend(issues)

    # Check invocation keyword args
    for (
        invocation_kwarg_name,
        invocation_kwarg_spec,
    ) in invocation_keyword_arg_specs.items():
        # Already checked for invalid keywords in kwarg invocations; may as
        # well not duplicate that check here.
        task_arg = task_inputs_map[invocation_kwarg_name]

        issues = _check_invocation_parameter(
            invocation_kwarg_spec,
            task_arg,
            type_reg,
            global_parameter_types,
            graph,
            tasks,
            artifact_inputs,
            state=state,
        )

        for issue in issues:
            prefix = state.message(
                'in keyword argument "', invocation_kwarg_name, '": '
            )
            issue.message = prefix + issue.message

        all_issues.extend(issues)

    return all_issues


def _check_global_parameter_defaults(
    global_parameter_spec: _DefMap,
    global_parameter_types: _TypeMap,
    state: TypeValidationState,
) -> list[ValidationIssue]:
    """
    Check global parameter default values for compatibility with their
    defined types (if any).

    Args:
        state: State shared by the current validation.
        global_parameter_spec: Global parameter specifications taken from an
            experiment description.  This maps a parameter name to a
            definition.
        global_parameter_types: A mapping from global parameter name to
            Type instance, giving the types of all global parameters

    Returns:
        A list of ValidationIssue objects; will be empty if no issues were
            found
    """
    # Can't really use None to mean no default, since that's a valid default!
    no_default = object()

    issues = []

    for (param_name, param_def), param_type in zip(
        # Rely on identical iteration order between the two maps
        global_parameter_spec.items(),
        global_parameter_types.values(),
    ):
        if isinstance(param_def, dict):
            param_default = param_def.get("default", no_default)
        else:
            param_default = param_def

        if param_default is not no_default:
            # Check the default against the type.
            default_type = _infer_type(param_default, state=state)

            if not _types_compatible(default_type, param_type, state=state):
                message = state.message(
                    'In global parameter "',
                    param_name,
                    '": default value is incompatible with its declared type: ',
                    state.describe(param_type),
                )

                issue = ValidationIssue(IssueType.TYPE, IssueSeverity.ERROR, message)
                issues.append(issue)

    return issues


def _infer_global_parameter_types(
    global_parameter_spec: _DefMap,
    type_reg: _TypeMap,
    state: TypeValidationState,
) -> _TypeMap:
    """
    Find types for all global parameters, either by looking up the type name
    if given, or inferring types from default values.

    Args:
        state: State shared by the current validation.
        global_parameter_spec: Global parameter specifications taken from an
            experiment description.  This maps a parameter name to a
            definition.
        type_reg: A type registry as a mapping from type name to Type instance

    Returns:
        A mapping from global parameter name to Type object representing the
            types of all global parameters.
    """
    global_parameter_types = {}

    for param_name, param_def in global_parameter_spec.items():
        if isinstance(param_def, dict):
            param_type_name = param_def.get("type")
            param_default = param_def.get("default")

        else:
            param_type_name = None
            param_default = param_def

        if param_type_name:
            param_type = type_reg[param_type_name]

        else:
            # Obtain a type by inference from a default value.  Assume that
            # if a type name is not given, a default value is given, i.e. that
            # check has already occurred.
            param_type = _infer_type(param_default, state=state)

        global_parameter_types[param_name] = param_type

    return global_parameter_types


def check_types_with_state(
    experiment_desc: Mapping[str, Any], state: TypeValidationState
) -> list[ValidationIssue]:
    """
    Check the types of all task invocation arguments across all steps in the
    task graph, against declared task plugin inputs and outputs.

    This interface is for engine validation phases that share state within one
    validation. Standalone callers should use check_types() instead.
    Resource-limit exceptions propagate so the engine stops subsequent phases.

    Args:
        experiment_desc: The experiment description, as parsed YAML or
            equivalent
        state: State owned by the current validation and shared between its phases.

    Returns:
        A list of ValidationIssue objects; will be empty if no issues were
        found

    Raises:
        ValidationLimitError: A resource limit was exceeded.
    """
    types_ = experiment_desc.get("types", {})
    global_parameter_spec = experiment_desc.get("parameters", {})
    tasks = experiment_desc["tasks"]
    graph = experiment_desc["graph"]
    artifact_inputs = experiment_desc.get("artifact_inputs", {})

    if state.registry is None:
        state.inspect(types_)
        state.registry = type_registry.build_type_registry(
            types_, check_message_length=state.check_message_length
        )
    type_reg = state.registry

    state.inspect(global_parameter_spec)
    state.inspect(graph)

    global_parameter_types = _infer_global_parameter_types(
        global_parameter_spec, type_reg, state=state
    )

    all_issues = _check_global_parameter_defaults(
        global_parameter_spec, global_parameter_types, state=state
    )

    if not all_issues:
        for step_name, step_def in graph.items():
            issues = _step_check_types(
                step_def,
                type_reg,
                global_parameter_types,
                graph,
                tasks,
                artifact_inputs,
                state=state,
            )

            for issue in issues:
                prefix = state.message('in step "', step_name, '": ')
                issue.message = prefix + issue.message

            all_issues.extend(issues)

    return all_issues


def check_types(
    experiment_desc: Mapping[str, Any],
    *,
    limits: TypeValidationLimits | None = None,
) -> list[ValidationIssue]:
    """Check task argument and global default types with fresh validation state.

    Args:
        experiment_desc: The experiment description, as parsed YAML or equivalent.
        limits: Resource limits for this validation. Defaults are used when omitted.

    Returns:
        Validation issues, including a type error if a resource limit is exceeded.
    """
    try:
        return check_types_with_state(experiment_desc, TypeValidationState(limits))
    except ValidationLimitError as error:
        return [ValidationLimitIssue(error)]
