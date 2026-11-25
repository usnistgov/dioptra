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
"""Check that complex workflows validate safely through supported entry points."""

import json
import subprocess
import sys
from collections import Counter
from dataclasses import replace
from typing import Any

import pytest

from dioptra.sdk.exceptions.task_engine import ValidationLimitError
from dioptra.sdk.utilities.entrypoint_swaps import (
    compile_swaps_config,
    render_swaps_config,
)
from dioptra.task_engine import type_validation
from dioptra.task_engine.issues import IssueSeverity, IssueType
from dioptra.task_engine.type_validation import check_types
from dioptra.task_engine.type_validation_state import (
    TypeValidationLimits,
    TypeValidationState,
)
from dioptra.task_engine.types import Type
from dioptra.task_engine.validation import schema_validate, validate


def workflow(value: Any = 1, steps: int = 1) -> dict[str, Any]:
    """Build a workflow whose steps all call the same task.

    Args:
        value: The argument each step passes to the task. Defaults to 1.
        steps: The number of calls to include in the graph. Defaults to one.

    Returns:
        A workflow dictionary containing the task, which expects a number,
        and a graph with one step per call.
    """
    return {
        "tasks": {
            "consume": {"plugin": "example.consume", "inputs": [{"value": "number"}]}
        },
        "graph": {f"step{i}": {"consume": [value]} for i in range(steps)},
    }


def ladder(depth: int, leaf: str = "number") -> dict[str, Any]:
    """Build a workflow that checks a boolean against nested unions.

    Args:
        depth: The number of levels of union types. Each level defines two
            unions with the same members. After the first level, both unions
            refer to the two unions in the level below.
        leaf: The type both unions at the first level contain. Use "boolean"
            for a match or the default "number" for a type mismatch.

    Returns:
        A workflow dictionary with the type definitions and one step that
        passes True to a task expecting the first union at the highest level.
        At depth zero, the task expects the leaf type directly.
    """
    definitions: dict[str, Any] = {}
    previous = [leaf]
    for level in range(depth):
        names = [f"level{level}a", f"level{level}b"]
        for name in names:
            definitions[name] = {"union": previous.copy()}
        previous = names
    config = workflow(True)
    config["types"] = definitions
    config["tasks"]["consume"]["inputs"] = [{"value": previous[0]}]
    return config


@pytest.fixture
def comparison_evaluations(
    monkeypatch: pytest.MonkeyPatch,
) -> Counter[tuple[str | None, str | None]]:
    """Count how often validation evaluates each pair of types.

    Args:
        monkeypatch: The pytest fixture that temporarily wraps the type
            comparison function and restores it after the test.

    Returns:
        A counter updated during validation. Each key contains the actual
        type name followed by the expected type name. Reusing a previous
        comparison leaves its count unchanged.
    """
    evaluations: Counter[tuple[str | None, str | None]] = Counter()
    evaluate = type_validation._evaluate_compatibility

    def record_evaluation(
        actual: Type, expected: Type, state: TypeValidationState
    ) -> bool:
        """Count this comparison and return the type checker's answer.

        Args:
            actual: The type supplied by the workflow.
            expected: The type required at this point in the workflow.
            state: The current validation's record of comparisons and limits.

        Returns:
            True if the supplied type fits the required type, otherwise False.
        """
        evaluations[actual.name, expected.name] += 1
        return evaluate(actual, expected, state)

    monkeypatch.setattr(type_validation, "_evaluate_compatibility", record_evaluation)
    return evaluations


def test_defaults_and_steps_reuse_successful_comparisons(
    comparison_evaluations: Counter[tuple[str | None, str | None]],
) -> None:
    """Reuse a successful type comparison across defaults and steps.

    The default and three task arguments all supply integers where a number is
    expected. Each validation call should evaluate that pair once.
    """
    config = workflow(steps=3)
    config["parameters"] = {"default": {"type": "number", "default": 1}}
    for _ in range(2):
        comparison_evaluations.clear()
        assert validate(config) == []
        assert comparison_evaluations["integer", "number"] == 1


def test_steps_reuse_failed_comparisons(
    comparison_evaluations: Counter[tuple[str | None, str | None]],
) -> None:
    """Reuse a failed type comparison while reporting every affected step.

    The default is valid, and three task arguments supply strings where a
    number is expected. Each validation call should evaluate the failing pair
    once and identify each incompatible step.
    """
    config = workflow("text", steps=3)
    config["parameters"] = {"default": {"type": "number", "default": 1}}
    for _ in range(2):
        comparison_evaluations.clear()
        issues = validate(config)

        assert comparison_evaluations["string", "number"] == 1
        assert len(issues) == len(config["graph"])
        assert all(issue.severity is IssueSeverity.ERROR for issue in issues)
        assert all("incompatible" in issue.message for issue in issues)
        for step_name in config["graph"]:
            assert any(f'"{step_name}"' in issue.message for issue in issues)


def test_invalid_default_is_reported_before_step_errors() -> None:
    """An invalid global default takes precedence over a step argument error.

    Both the default and the argument supply text where a number is required. The
    caller should receive a single error identifying the global parameter.
    """
    config = workflow("text")
    config["parameters"] = {"default": {"type": "number", "default": "text"}}
    issues = validate(config)
    assert len(issues) == 1
    assert issues[0].severity is IssueSeverity.ERROR
    assert 'In global parameter "default"' in issues[0].message


@pytest.mark.parametrize(
    ("definitions", "expected_details"),
    [
        (
            {"Status": {"union": ["string", "MissingStatus"]}},
            ("Status", "undefined type", "MissingStatus"),
        ),
        (
            {"LabelCounts": {"mapping": ["boolean", "integer"]}},
            ("LabelCounts", "key type", "boolean"),
        ),
        (
            {
                "Labels": {"list": "string"},
                "SpecialLabels": {"is_a": "Labels"},
            },
            ("SpecialLabels", "Super-types must be simple", "Labels"),
        ),
        (
            {"NestedItems": {"list": "NestedItems"}},
            ("cycle", "NestedItems"),
        ),
    ],
    ids=["undefined-type", "invalid-key", "invalid-supertype", "cycle"],
)
def test_type_definition_diagnostics_respect_allowance(
    definitions: dict[str, Any], expected_details: tuple[str, ...]
) -> None:
    """Report type-definition errors within the diagnostic allowance.

    Each invalid definition yields a semantic error that identifies the
    problem. A smaller allowance produces a single limit error instead.
    """
    config = workflow()
    config["types"] = definitions

    (issue,) = validate(config)
    assert issue.type is IssueType.SEMANTIC
    assert issue.severity is IssueSeverity.ERROR
    assert all(detail in issue.message for detail in expected_details)

    limits = replace(TypeValidationLimits(), diagnostic_characters=32)
    (issue,) = validate(config, limits=limits)
    assert issue.type is IssueType.TYPE
    assert issue.severity is IssueSeverity.ERROR
    assert "diagnostic size limit" in issue.message


def test_undefined_type_diagnostics_share_allowance() -> None:
    """Apply the diagnostic allowance to all undefined type references.

    Each message fits by itself. Reporting both together would exhaust the
    allowance, so the caller receives one diagnostic-limit error.
    """
    config = workflow()
    config["types"] = {
        "Statuses": {"list": "MissingStatus"},
        "Labels": {"list": "MissingLabel"},
    }

    issues = validate(config)
    assert len(issues) == 2
    limits = replace(
        TypeValidationLimits(),
        diagnostic_characters=max(len(issue.message) for issue in issues),
    )

    (issue,) = validate(config, limits=limits)
    assert issue.type is IssueType.TYPE
    assert issue.severity is IssueSeverity.ERROR
    assert "diagnostic size limit" in issue.message


@pytest.mark.parametrize("check", [validate, check_types])
@pytest.mark.parametrize(
    "limits,config,resource",
    [
        (replace(TypeValidationLimits(), work=3), workflow(steps=11), "work"),
        (
            replace(TypeValidationLimits(), cache_entries=1),
            ladder(4),
            "comparison cache",
        ),
        (
            replace(TypeValidationLimits(), comparison_depth=4),
            ladder(8),
            "comparison nesting",
        ),
        (replace(TypeValidationLimits(), input_nodes=3), workflow(), "input size"),
        (replace(TypeValidationLimits(), input_characters=3), workflow(), "input text"),
        (
            replace(TypeValidationLimits(), input_depth=3),
            workflow([[1]]),
            "input nesting",
        ),
        (
            replace(TypeValidationLimits(), diagnostic_nodes=1),
            workflow([1, 2]),
            "diagnostic traversal",
        ),
        (
            replace(TypeValidationLimits(), diagnostic_characters=200),
            workflow("text", 11),
            "diagnostic size",
        ),
    ],
)
def test_exceeded_limit_returns_one_short_error(
    check, limits, config, resource
) -> None:
    """Callers should receive one short error identifying the limit they reached.

    Each case lowers one limit enough for the workflow to exceed it. Full
    validation and standalone type checking should both name that resource in the
    error.
    """
    issues = check(config, limits=limits)
    assert len(issues) == 1
    assert issues[0].type is IssueType.TYPE
    assert issues[0].severity is IssueSeverity.ERROR
    assert f"{resource} limit" in issues[0].message
    assert len(issues[0].message) < 100


@pytest.mark.parametrize("depth", [4, 8, 12, 16])
@pytest.mark.parametrize("compatible", [False, True])
def test_named_union_ladder_finishes_with_linear_work_budget(depth, compatible) -> None:
    """Checking unions that share members should take limited work at each level.

    Each level refers to the same two types from the level below. An allowance
    proportional to the number of levels should be enough to accept a matching
    value or report a mismatch.
    """
    config = ladder(depth, "boolean" if compatible else "number")
    # A budget proportional to input depth permits bookkeeping changes but not
    # exponential recomputation. A separate subprocess test bounds elapsed time.
    issues = validate(config, limits=replace(TypeValidationLimits(), work=32 * depth))
    if compatible:
        assert issues == []
    else:
        assert len(issues) == 1
        assert "incompatible" in issues[0].message


def test_unions_on_both_sides_finish_within_work_limit() -> None:
    """Validation should report a mismatch when both tasks declare union types.

    The producing task returns text or a boolean. The consuming task accepts
    several layers of unions that ultimately require a number. The work allowance
    should be enough to reach the type error.
    """
    config = ladder(8)
    config["types"]["Source"] = {"union": ["string", "boolean"]}
    config["tasks"]["produce"] = {
        "plugin": "example.produce",
        "outputs": [{"value": "Source"}],
    }
    config["graph"] = {
        "produce": {"produce": []},
        "consume": {"consume": ["$produce.value"]},
    }
    issues = validate(config, limits=replace(TypeValidationLimits(), work=2_000))
    assert len(issues) == 1
    assert "incompatible" in issues[0].message


@pytest.mark.parametrize("section", ["types", "parameters", "graph"])
def test_nested_input_is_rejected_by_engine_and_sdk(section) -> None:
    """The engine and SDK must recognize input that is nested too deeply.

    The nesting can occur in a type definition, a parameter default, or a step
    argument. All checked paths should report the default nesting limit. Raising
    that limit in the engine should let ordinary schema and type checks proceed.
    """
    config = workflow()
    nested: Any = "number" if section == "types" else 1
    for _ in range(30):
        nested = {"list": nested} if section == "types" else [nested]
    if section == "types":
        config["types"] = {"Nested": nested}
    elif section == "parameters":
        config["parameters"] = {"value": {"default": nested}}
    else:
        config["graph"]["step0"] = {"consume": [nested]}

    for check in (schema_validate, validate, check_types):
        issues = check(config)
        assert len(issues) == 1
        assert "input nesting" in issues[0].message
    with pytest.raises(ValidationLimitError, match="input nesting"):
        compile_swaps_config(config)
    with pytest.raises(ValidationLimitError, match="input nesting"):
        render_swaps_config(config, {})

    # Raising the input limit must also apply to full validation's schema preflight.
    limits = replace(TypeValidationLimits(), input_depth=64)
    assert schema_validate(config, limits=limits) == []
    issues = validate(config, limits=limits)
    assert all("limit" not in issue.message for issue in issues)
    assert [issue.message for issue in issues] == [
        issue.message for issue in check_types(config, limits=limits)
    ]


def test_repeated_aliases_count_towards_input_limit() -> None:
    """Each occurrence of a shared list counts toward the input size limit.

    The argument refers to the same list many times. The list fits on its own, but
    validating all occurrences should produce one input size error.
    """
    shared = [1] * 100
    issues = validate(
        workflow([shared] * 100),
        limits=replace(TypeValidationLimits(), input_nodes=500),
    )
    assert len(issues) == 1
    assert "input size" in issues[0].message


def test_cyclic_input_returns_nesting_error() -> None:
    """A list containing itself should produce a nesting error.

    A Python caller can pass this list directly as a step argument. Validation
    should stop and return one error even though following the list would never
    reach a final value.
    """
    value: list[Any] = []
    value.append(value)
    issues = validate(workflow(value))
    assert len(issues) == 1
    assert "input nesting" in issues[0].message


def test_named_diagnostics_use_short_type_names() -> None:
    """A type mismatch should identify a deeply nested union by its declared name.

    The step supplies a boolean where the union ultimately requires a number. The
    error should include the name used by the task and stay short.
    """
    issues = validate(ladder(16))
    assert len(issues) == 1
    assert len(issues[0].message) < 300
    assert "level15a" in issues[0].message


def test_anonymous_diagnostics_are_shortened() -> None:
    """A large value without a declared type should still produce a short error.

    The step supplies a hundred integers as a list where a single number is
    required. The message should explain the incompatibility within a thousand
    characters.
    """
    issues = validate(workflow([1] * 100))
    assert len(issues) == 1
    assert "incompatible" in issues[0].message
    assert len(issues[0].message) < 1_000


def test_named_union_ladder_finishes_before_timeout() -> None:
    """Validation should finish when many unions refer to the same types.

    The step supplies a boolean to a union that ultimately requires a number.
    Running validation in a separate process gives it 15 seconds to report
    that mismatch before the test times out.
    """
    script = (
        "import json, sys\n"
        "from dioptra.task_engine.validation import validate\n"
        "issues = validate(json.load(sys.stdin))\n"
        "print(json.dumps([issue.message for issue in issues]))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        input=json.dumps(ladder(32)),
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    messages = json.loads(result.stdout)
    assert len(messages) == 1
    assert "incompatible" in messages[0]


def test_early_guard_ignores_unrelated_data_under_a_custom_schema() -> None:
    """Unrelated metadata should pass validation under a schema that permits it.

    The document contains a large metadata list and the supplied schema accepts
    any object. The size of that list should not produce a workflow validation
    error.
    """
    config = {"metadata": [None] * 25_000}
    assert schema_validate(config, {"type": "object"}) == []


def test_duplicate_warning_uses_short_type_names() -> None:
    """A duplicate union member should be identified by name in a short warning.

    The repeated member is itself a union built from several layers of types. The
    warning should name that member without expanding its definition.
    """
    config = ladder(8, "boolean")
    config["types"]["Duplicates"] = {"union": ["level7a", "level7a"]}
    issues = validate(config)
    assert len(issues) == 1
    assert issues[0].severity is IssueSeverity.WARNING
    assert "level7a" in issues[0].message
    assert len(issues[0].message) < 300


def test_subtype_traversal_respects_work_limit() -> None:
    """Following parent types counts toward the work allowed for validation.

    The output type descends from the numeric type the input requires. With too
    little work allowed to follow the chain, validation should report the work
    limit.
    """
    config = workflow("$source.value")
    config["types"] = {
        f"Child{i}": {"is_a": f"Child{i - 1}" if i else "number"} for i in range(20)
    }
    config["tasks"]["source"] = {
        "plugin": "example.source",
        "outputs": {"value": "Child19"},
    }
    config["graph"]["source"] = {"source": []}
    issues = validate(config, limits=replace(TypeValidationLimits(), work=10))
    assert len(issues) == 1
    assert "work limit" in issues[0].message


@pytest.mark.parametrize("depth,exceeded", [(63, False), (64, True)])
def test_default_comparison_depth_boundary_without_branching(depth, exceeded) -> None:
    """The default comparison depth allows a mismatch to be found through 63 unions.

    Each union has just one member, and the final type requires a number where the
    step supplies text. Adding a 64th union should change the reported error from
    a type mismatch to the comparison nesting limit.
    """
    # A single-child chain stays cheap even if caching regresses.
    config = workflow("text")
    config["types"] = {
        f"Level{i}": {"union": [f"Level{i - 1}" if i else "number"]}
        for i in range(depth)
    }
    config["tasks"]["consume"]["inputs"] = [{"value": f"Level{depth - 1}"}]
    issues = validate(config)
    assert len(issues) == 1
    expected = "comparison nesting" if exceeded else "incompatible"
    assert expected in issues[0].message
