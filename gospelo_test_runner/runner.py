"""Test runner - orchestrates test case execution with filtering, logging, and reporting."""

from __future__ import annotations

import sys
import time
from datetime import datetime
from typing import Callable

from .types import TestCase, TestResult, TestStatus, TestSuiteConfig
from .executor.base import BaseExecutor
from .reporter.json_reporter import JsonReporter
from .reporter.log_reporter import LogReporter


# ---------------------------------------------------------------------------
# Color support — auto-detect TTY, disabled when output is redirected/piped
# ---------------------------------------------------------------------------

def _supports_color() -> bool:
    """Return True if stdout is a TTY that likely supports ANSI color."""
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    if sys.platform == "win32":
        try:
            import os
            return os.environ.get("ANSICON") is not None or "WT_SESSION" in os.environ
        except Exception:
            return False
    return True


_COLOR_ENABLED = _supports_color()


def _c(code: str, text: str) -> str:
    """Wrap text with ANSI color code if color is enabled."""
    if not _COLOR_ENABLED:
        return text
    return f"\033[{code}m{text}\033[0m"


# Status display labels (no emoji per project rules)
STATUS_LABELS = {
    TestStatus.OK: "[OK]",
    TestStatus.NG: "[NG]",
    TestStatus.ERROR: "[!!]",
    TestStatus.INFO: "[--]",
    TestStatus.SKIP: "[--]",
}

# ANSI color codes per status
_STATUS_COLORS: dict[TestStatus, str] = {
    TestStatus.OK: "32",      # green
    TestStatus.NG: "31",      # red
    TestStatus.ERROR: "1;31", # bold red
    TestStatus.INFO: "36",    # cyan
    TestStatus.SKIP: "90",    # dim gray
}


def print_result(result: TestResult) -> None:
    """Pretty-print a test result to stdout."""
    label = STATUS_LABELS.get(result.status, "[??]")
    color = _STATUS_COLORS.get(result.status, "0")
    print(f"  {_c(color, label)} {result.test_id}: {result.message}")


def run_tests(
    suite_config: TestSuiteConfig,
    cases: list[TestCase],
    executor: BaseExecutor,
    *,
    on_result: Callable[[TestResult], None] | None = None,
) -> list[TestResult]:
    """Execute test cases and collect results.

    This is the core orchestration function. It handles:
    - Test case filtering (by test_id or category)
    - Dry-run mode
    - Delay between test cases
    - Result collection and display

    Args:
        suite_config: Test suite configuration.
        cases: List of test cases to execute.
        executor: Executor instance for running tests.
        on_result: Optional callback invoked after each test result.

    Returns:
        List of TestResult objects.
    """
    filtered = _filter_cases(
        cases,
        test_id=suite_config.test_id_filter,
        category=suite_config.category_filter,
    )

    if not filtered:
        print(f"No test cases matched the filter. Total cases: {len(cases)}")
        return []

    header_bar = _c("1;36", "=" * 60)
    print(f"\n{header_bar}")
    print(f"  {_c('1', suite_config.test_name)}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Cases: {len(filtered)} / {len(cases)}")
    if suite_config.dry_run:
        print(f"  Mode: {_c('33', 'DRY-RUN')}")
    print(f"{header_bar}\n")

    executor.setup()
    results: list[TestResult] = []

    try:
        current_category = ""
        for i, case in enumerate(filtered):
            if case.category != current_category:
                current_category = case.category
                print(f"\n--- {current_category} ---")

            result = executor.execute(case, dry_run=suite_config.dry_run)
            results.append(result)

            if on_result:
                on_result(result)

            print_result(result)

            if i < len(filtered) - 1 and not suite_config.dry_run:
                time.sleep(suite_config.delay)
    finally:
        executor.teardown()

    _print_summary(results)
    return results


def run_suite(
    suite_config: TestSuiteConfig,
    cases: list[TestCase],
    executor: BaseExecutor,
    *,
    on_result: Callable[[TestResult], None] | None = None,
    enable_log: bool = True,
    enable_json: bool = True,
) -> list[TestResult]:
    """Execute test suite with full evidence collection (log + JSON).

    This is the high-level entry point that combines:
    - Log capture (evidence_*.log)
    - Test execution
    - JSON evidence output (evidence_*.json)

    Args:
        suite_config: Test suite configuration.
        cases: List of test cases to execute.
        executor: Executor instance for running tests.
        on_result: Optional callback invoked after each test result.
        enable_log: Enable log file capture (default: True).
        enable_json: Enable JSON evidence output (default: True).

    Returns:
        List of TestResult objects.
    """
    log_reporter = LogReporter(suite_config.output_dir, suite_config.evidence_name) if enable_log else None
    json_reporter = JsonReporter(suite_config.output_dir, suite_config.test_name, suite_config.evidence_name) if enable_json else None

    if log_reporter:
        log_path = log_reporter.start()
        print(f"Log: {log_path}")

    try:
        results = run_tests(suite_config, cases, executor, on_result=on_result)
    finally:
        if log_reporter:
            log_reporter.stop()

    if json_reporter and results and not suite_config.dry_run:
        json_path = json_reporter.write(
            results,
            executor=suite_config.config.get("executor", ""),
            region=suite_config.config.get("region", ""),
        )
        print(f"\nEvidence JSON: {json_path}")

    if log_reporter and log_reporter.log_path:
        print(f"Evidence Log:  {log_reporter.log_path}")

    return results


def list_cases(cases: list[TestCase]) -> None:
    """Print test case list without executing."""
    print(f"\nTest cases ({len(cases)}):\n")
    current_category = ""
    for case in cases:
        if case.category != current_category:
            current_category = case.category
            print(f"\n  [{current_category}]")
        print(f"    {case.test_id}: {case.description}")


def _filter_cases(
    cases: list[TestCase],
    test_id: str | None = None,
    category: str | None = None,
) -> list[TestCase]:
    """Filter test cases by test_id or category prefix."""
    if test_id:
        return [c for c in cases if c.test_id == test_id]
    if category:
        return [c for c in cases if c.category.startswith(category)]
    return list(cases)


def _print_summary(results: list[TestResult]) -> None:
    """Print result summary."""
    total = len(results)
    counts = {s: 0 for s in TestStatus}
    for r in results:
        counts[r.status] += 1

    has_failures = counts[TestStatus.NG] + counts[TestStatus.ERROR] > 0
    bar = _c("31", "=" * 60) if has_failures else _c("32", "=" * 60)

    print(f"\n{bar}")
    print(f"  Results: {total} total")
    for status, count in counts.items():
        if count > 0:
            label = STATUS_LABELS.get(status, "[??]")
            color = _STATUS_COLORS.get(status, "0")
            print(f"    {_c(color, label)} {status.value}: {count}")
    print(bar)
