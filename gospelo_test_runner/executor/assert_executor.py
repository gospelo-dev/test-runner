"""Assert executor for self-testing and validation scenarios.

Evaluates Python expressions against config values — useful for
configuration validation, environment checks, and harness self-tests.

TestCase.params keys:
    actual: The actual value to evaluate (supports {{config.key}} interpolation)
    expected: The expected value
    operator: Comparison operator (default: "eq")
              eq / ne / contains / not_contains / gt / lt / ge / le / is_truthy / is_falsy / matches
    message: Optional failure message
"""

from __future__ import annotations

import re
from typing import Any

from .base import BaseExecutor
from ..types import TestCase, TestResult, TestStatus


class AssertExecutor(BaseExecutor):
    """Execute assertion-based test cases.

    Compares actual vs expected values using configurable operators.
    Supports config value interpolation via {{config.key}} syntax.
    """

    def execute(self, case: TestCase, dry_run: bool = False) -> TestResult:
        params = case.params
        actual = self._interpolate(params.get("actual", ""))
        expected = params.get("expected")
        operator = params.get("operator", "eq")
        fail_message = params.get("message", "")

        if dry_run:
            return TestResult(
                test_id=case.test_id,
                status=TestStatus.SKIP,
                message="[DRY-RUN]",
                details=self.get_dry_run_info(case),
            )

        try:
            passed, detail = self._evaluate(actual, expected, operator)

            status = TestStatus.OK if passed else TestStatus.NG
            message = detail if passed else (fail_message or detail)

            return TestResult(
                test_id=case.test_id,
                status=status,
                message=message,
                details={
                    "actual": actual,
                    "expected": expected,
                    "operator": operator,
                    "passed": passed,
                },
            )

        except Exception as e:
            return TestResult(
                test_id=case.test_id,
                status=TestStatus.ERROR,
                message=f"{type(e).__name__}: {e}",
                details={
                    "actual": actual,
                    "expected": expected,
                    "operator": operator,
                    "error": str(e),
                },
            )

    def _interpolate(self, value: Any) -> Any:
        """Replace {{config.key}} with actual config values."""
        if not isinstance(value, str):
            return value

        def replacer(match: re.Match) -> str:
            key = match.group(1)
            return str(self.suite_config.config.get(key, f"<missing:{key}>"))

        return re.sub(r"\{\{config\.(\w+)\}\}", replacer, value)

    def _evaluate(self, actual: Any, expected: Any, operator: str) -> tuple[bool, str]:
        """Evaluate the assertion and return (passed, message)."""
        ops: dict[str, tuple[Any, str]] = {
            "eq": (actual == expected, f"{actual!r} == {expected!r}"),
            "ne": (actual != expected, f"{actual!r} != {expected!r}"),
            "contains": (expected in str(actual), f"{expected!r} in {str(actual)!r}"),
            "not_contains": (expected not in str(actual), f"{expected!r} not in {str(actual)!r}"),
            "gt": (float(actual) > float(expected), f"{actual} > {expected}"),
            "lt": (float(actual) < float(expected), f"{actual} < {expected}"),
            "ge": (float(actual) >= float(expected), f"{actual} >= {expected}"),
            "le": (float(actual) <= float(expected), f"{actual} <= {expected}"),
            "is_truthy": (bool(actual), f"bool({actual!r}) is True"),
            "is_falsy": (not bool(actual), f"bool({actual!r}) is False"),
            "matches": (bool(re.search(str(expected), str(actual))), f"{str(actual)!r} matches {expected!r}"),
        }

        if operator not in ops:
            raise ValueError(f"Unknown operator: {operator!r}. Available: {sorted(ops.keys())}")

        passed, msg = ops[operator]
        return passed, msg

    def get_dry_run_info(self, case: TestCase) -> dict[str, Any]:
        params = case.params
        return {
            "test_id": case.test_id,
            "actual": params.get("actual"),
            "expected": params.get("expected"),
            "operator": params.get("operator", "eq"),
        }
