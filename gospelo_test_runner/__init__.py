"""gospelo-test-runner: Generic test execution harness with pluggable executors."""

from .types import TestCase, TestResult, TestStatus, TestSuiteConfig, TestSuiteMeta
from .runner import run_tests, run_suite, list_cases
from .executor.base import BaseExecutor
from .executor.http_executor import HttpExecutor
from .executor.process_executor import ProcessExecutor
from .loader.config_loader import load_config
from .loader.spec_loader import load_spec_json, load_spec_yml, load_prereq_json
from .reporter.json_reporter import JsonReporter
from .reporter.log_reporter import LogReporter
from .reporter.spec_exporter import export_test_spec
from .executor.registry import get_executor_class, list_executors
from .version import get_version_info, version_stamp, FORMAT_VERSION

__version__ = "0.1.0"

__all__ = [
    # Types
    "TestCase",
    "TestResult",
    "TestStatus",
    "TestSuiteConfig",
    "TestSuiteMeta",
    # Runner
    "run_tests",
    "run_suite",
    "list_cases",
    # Executors
    "BaseExecutor",
    "HttpExecutor",
    "ProcessExecutor",
    # Loaders
    "load_config",
    "load_spec_json",
    "load_spec_yml",
    "load_prereq_json",
    # Reporters
    "JsonReporter",
    "LogReporter",
    "export_test_spec",
    # Executor Registry
    "get_executor_class",
    "list_executors",
    # Version
    "get_version_info",
    "version_stamp",
    "FORMAT_VERSION",
]
