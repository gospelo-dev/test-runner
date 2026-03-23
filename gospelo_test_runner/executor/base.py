"""Base executor interface for test case execution."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..types import TestCase, TestResult, TestSuiteConfig


class BaseExecutor(ABC):
    """Abstract base class for test executors.

    Subclass this to implement different execution strategies:
    - HTTP request execution
    - AWS SDK (boto3) calls
    - Static analysis
    - Subprocess execution
    """

    def __init__(self, suite_config: TestSuiteConfig) -> None:
        self.suite_config = suite_config

    @abstractmethod
    def execute(self, case: TestCase, dry_run: bool = False) -> TestResult:
        """Execute a single test case and return the result.

        Args:
            case: The test case to execute.
            dry_run: If True, prepare and display the request without sending.

        Returns:
            TestResult with status, message, and evidence details.
        """
        ...

    def setup(self) -> None:
        """Optional setup hook called before the first test case."""

    def teardown(self) -> None:
        """Optional teardown hook called after the last test case."""

    def get_dry_run_info(self, case: TestCase) -> dict[str, Any]:
        """Return request preview info for dry-run mode.

        Override this to provide executor-specific dry-run output.
        """
        return {
            "test_id": case.test_id,
            "category": case.category,
            "description": case.description,
            "params": case.params,
        }
