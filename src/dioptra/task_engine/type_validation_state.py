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
"""Track resource use during one type validation.

Limits count operations and input size; they do not measure memory or elapsed time.
"""

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from itertools import chain
from typing import Any, NoReturn

from dioptra.sdk.exceptions.task_engine import ValidationLimitError
from dioptra.task_engine import types


@dataclass(frozen=True)
class TypeValidationLimits:
    """Resource limits for one validation, safe to reuse across calls."""

    # Distinct comparisons retained, including pending and completed results.
    cache_entries: int = 10_000
    # Total counted operations, including cache lookups and traversal visits.
    work: int = 100_000
    # Compatibility comparisons nested inside unfinished comparisons.
    comparison_depth: int = 64
    # Input items visited, including containers, keys, values, and repeat visits.
    input_nodes: int = 20_000
    # Container nesting in inspected input; named references are not expanded.
    input_depth: int = 24
    # Total string characters encountered during input inspection.
    input_characters: int = 1_000_000
    # Type nodes visited while constructing mismatch and duplicate diagnostics.
    diagnostic_nodes: int = 1_024
    # Aggregate diagnostic characters constructed, including context prefixes.
    diagnostic_characters: int = 16_384


@dataclass
class Comparison:
    """Store a type pair and its compatibility result.

    A result of None means the comparison has not finished. Keep both type
    objects alive because the cache uses their object IDs as keys.
    """

    argument: types.Type
    parameter: types.Type
    result: bool | None = None


class TypeValidationState:
    """Store cached comparisons and resource usage for one validation.

    Public validation entry points create this state and share it between their
    internal phases. It must not be reused for another configuration.

    Counters accumulate across phases. Exceeding a limit raises
    ValidationLimitError and marks validation as stopped.
    """

    def __init__(self, limits: TypeValidationLimits | None = None) -> None:
        self.limits = limits or TypeValidationLimits()
        self.comparisons: dict[tuple[int, int], Comparison] = {}
        self.registry: Mapping[str, types.Type] | None = None
        self.work = 0
        self.depth = 0
        self.input_nodes = 0
        self.input_characters = 0
        self.diagnostic_nodes = 0
        self.diagnostic_characters = 0
        self.exhausted = False

    def fail(self, resource: str) -> NoReturn:
        """Mark validation as stopped and raise ValidationLimitError."""
        self.exhausted = True
        raise ValidationLimitError(resource)

    def charge(self) -> None:
        """Count one operation before performing it; reject work after a failure."""
        if self.exhausted or self.work >= self.limits.work:
            self.fail("work")
        self.work += 1

    def members(self, values: Iterable[Any]) -> Iterator[Any]:
        """Yield members, counting each visit against the work limit."""
        for value in values:
            self.charge()
            yield value

    def inspect(self, value: Any) -> None:
        """Check input size and nesting before recursive processing.

        Count shared values on each occurrence, as schema validation and type
        inference do. Walk iteratively to avoid exhausting Python's call stack;
        cycles reach the nesting limit. Type names remain strings, without
        following their definitions.
        """
        stack = [iter((value,))]
        while stack:
            try:
                item = next(stack[-1])
            except StopIteration:
                stack.pop()
                continue
            self._count_input(item)
            if not isinstance(item, (Mapping, list, tuple)):
                continue
            if len(stack) >= self.limits.input_depth:
                self.fail("input nesting")
            children = (
                chain.from_iterable(item.items())
                if isinstance(item, Mapping)
                else iter(item)
            )
            stack.append(children)

    def _count_input(self, value: Any) -> None:
        """Account for one visited item, including text in mapping keys/values."""
        if self.exhausted or self.input_nodes >= self.limits.input_nodes:
            self.fail("input size")
        self.input_nodes += 1
        if not isinstance(value, str):
            return
        self.input_characters += len(value)
        if self.input_characters > self.limits.input_characters:
            self.fail("input text")

    def message(self, *parts: str) -> str:
        """Join message parts, checking the total diagnostic character limit."""
        size = sum(map(len, parts))
        self.check_message_length(size)
        self.diagnostic_characters += size
        return "".join(parts)

    def check_message_length(self, size: int) -> None:
        """Check whether text of this size fits without charging the allowance."""
        if self.exhausted or (
            self.diagnostic_characters + size > self.limits.diagnostic_characters
        ):
            self.fail("diagnostic size")

    def describe(self, type_: types.Type) -> str:
        """Describe a type using its name or a shortened structural description.

        Count visited types against the diagnostic limit instead of using
        str/repr, which can expand nested types repeatedly.
        """
        formatter = _TypeFormatter(self)
        formatter.visit(type_, 0)
        return "".join(formatter.parts) + ("..." if not formatter.remaining else "")


class _TypeFormatter:
    """Shorten type descriptions and count the types visited while formatting."""

    def __init__(self, state: TypeValidationState) -> None:
        self.state = state
        self.parts: list[str] = []
        self.remaining = 512

    def append(self, text: str) -> None:
        piece = text[: self.remaining]
        self.parts.append(piece)
        self.remaining -= len(piece)

    def visit(self, current: types.Type, depth: int) -> None:
        if not self.remaining:
            return
        if self.state.diagnostic_nodes >= self.state.limits.diagnostic_nodes:
            self.state.fail("diagnostic traversal")
        self.state.diagnostic_nodes += 1
        if current.name is not None:
            self.append(current.name)
        elif depth >= 4:
            self.append("...")
        elif isinstance(current, types.UnionType):
            self.append("UNION[")
            self.visit_members(current.member_types, depth)
            self.append("]")
        elif isinstance(current, types.StructuredType):
            self.visit_structure(current.structure, depth)

    def visit_structure(self, structure: types.TypeStructure, depth: int) -> None:
        self.append(structure.struct_type.name + "[")
        definition = structure.struct_def
        if isinstance(definition, types.Type):
            self.visit(definition, depth + 1)
        elif isinstance(definition, Mapping):
            for name, child in definition.items():
                if not self.remaining:
                    break
                self.append(name)
                self.append(": ")
                self.visit(child, depth + 1)
                self.append(", ")
        else:
            self.visit_members(definition, depth)
        self.append("]")

    def visit_members(self, members: Iterable[types.Type], depth: int) -> None:
        for index, member in enumerate(members):
            if not self.remaining:
                break
            if index:
                self.append(", ")
            self.visit(member, depth + 1)


def check_validation_input(
    config: Mapping[str, Any], *, limits: TypeValidationLimits | None = None
) -> None:
    """Check types and values before recursive schema validation or copying.

    Args:
        config: Configuration whose types, parameters, and graph need inspection.
        limits: Resource limits for this input check. Defaults are used when omitted.

    Raises:
        ValidationLimitError: Input size or nesting exceeds a resource limit.
    """
    state = TypeValidationState(limits)
    for section in ("types", "parameters", "graph"):
        if section in config:
            state.inspect(config[section])
