"""Subprocess executor for running external commands as tests."""

from __future__ import annotations

import subprocess
from typing import Any

from .base import BaseExecutor
from ..types import TestCase, TestResult, TestStatus


class ProcessExecutor(BaseExecutor):
    """Execute test cases by running external commands.

    Useful for static analysis tools, CLI-based scanners, or
    wrapping existing test scripts.

    TestCase.params keys:
        command: list[str] command and arguments
        cwd: Working directory (default: current directory)
        timeout: Timeout in seconds (default: 60)
        expected_returncode: Expected return code (default: 0)
        env: dict of environment variable overrides
    """

    def execute(self, case: TestCase, dry_run: bool = False) -> TestResult:
        params = case.params
        command = params.get("command", [])
        cwd = params.get("cwd")
        timeout = params.get("timeout", 60)
        expected_rc = params.get("expected_returncode", 0)
        env = params.get("env")

        if not command:
            return TestResult(
                test_id=case.test_id,
                status=TestStatus.ERROR,
                message="No command specified in params",
            )

        if dry_run:
            return TestResult(
                test_id=case.test_id,
                status=TestStatus.SKIP,
                message="[DRY-RUN]",
                details=self.get_dry_run_info(case),
            )

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env=env,
            )

            status = TestStatus.OK if result.returncode == expected_rc else TestStatus.NG

            return TestResult(
                test_id=case.test_id,
                status=status,
                message=f"exit={result.returncode} (expected={expected_rc})",
                details={
                    "command": command,
                    "returncode": result.returncode,
                    "expected_returncode": expected_rc,
                    "stdout": result.stdout[:2000] if result.stdout else "",
                    "stderr": result.stderr[:2000] if result.stderr else "",
                },
            )

        except subprocess.TimeoutExpired:
            return TestResult(
                test_id=case.test_id,
                status=TestStatus.ERROR,
                message=f"Command timed out after {timeout}s",
                details={"command": command, "timeout": timeout},
            )

        except Exception as e:
            return TestResult(
                test_id=case.test_id,
                status=TestStatus.ERROR,
                message=f"{type(e).__name__}: {e}",
                details={"command": command, "error": str(e)},
            )

    def get_dry_run_info(self, case: TestCase) -> dict[str, Any]:
        params = case.params
        return {
            "test_id": case.test_id,
            "command": params.get("command", []),
            "cwd": params.get("cwd"),
            "expected_returncode": params.get("expected_returncode", 0),
        }
