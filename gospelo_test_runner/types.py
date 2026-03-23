"""Core type definitions for the test engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TestStatus(Enum):
    """Test result status."""

    OK = "OK"
    NG = "NG"
    ERROR = "ERROR"
    INFO = "INFO"
    SKIP = "SKIP"


@dataclass
class TestCase:
    """A single test case definition.

    Attributes:
        test_id: Unique identifier (e.g., "HI-01")
        category: Test category / group name
        description: Human-readable description of the test
        test_type: Type of test (e.g., "HTTP", "API", "Static")
        expected_result: Expected outcome description
        params: Flexible key-value parameters for test-specific data
    """

    test_id: str
    category: str
    description: str
    test_type: str = ""
    expected_result: str = ""
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResult:
    """Result of a single test case execution.

    Attributes:
        test_id: Identifier matching the TestCase
        status: OK / NG / ERROR / INFO / SKIP
        message: Human-readable result summary
        details: Structured result data (request/response, timings, etc.)
        evidence: Raw evidence data for reporting
    """

    test_id: str
    status: TestStatus
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestSuiteConfig:
    """Configuration for a test suite execution.

    Attributes:
        test_name: Display name of the test suite
        test_id_prefix: ID prefix for the suite (e.g., "03_header_injection")
        script_prefix: Script directory prefix
        config: Loaded configuration values from yml/JSON
        output_dir: Directory for evidence output
        dry_run: If True, show requests without executing
        delay: Delay between test cases (seconds)
        test_id_filter: Run only matching test ID
        category_filter: Run only matching category prefix
    """

    test_name: str
    test_id_prefix: str
    script_prefix: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    output_dir: str = "logs"
    dry_run: bool = False
    delay: float = 1.0
    test_id_filter: str | None = None
    category_filter: str | None = None
    evidence_name: str = ""


@dataclass
class TestSuiteMeta:
    """Metadata envelope for test results output."""

    test_name: str
    timestamp: str
    executor: str = ""
    region: str = ""
    environment: dict[str, str] = field(default_factory=dict)
    summary: dict[str, int] = field(default_factory=dict)
