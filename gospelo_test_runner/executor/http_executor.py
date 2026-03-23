"""HTTP request executor for API testing."""

from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
import urllib.error
from typing import Any

from .base import BaseExecutor
from ..types import TestCase, TestResult, TestStatus

_PLACEHOLDER_RE = re.compile(r"\{config\.([^}]+)\}")


class HttpExecutor(BaseExecutor):
    """Execute test cases via HTTP requests.

    Supports GET, POST, PUT, PATCH, DELETE methods with configurable
    headers, body, and timeout. Evaluates responses against expected
    status codes.

    TestCase.params keys:
        method: HTTP method (default: "GET")
        url/path: Full URL or path (appended to base_url from config)
        headers: dict of request headers
        body: Request body (dict or string)
        query_params: dict of query parameters (appended to URL)
        expected_status: list[int] of acceptable status codes
        no_auth: If True, skip Authorization header
        timeout: Request timeout in seconds (default: 10)

    Config keys used:
        base_url: Base URL for relative paths
        token: Token for Authorization header
        auth_scheme: Authorization scheme (default: "Bearer")
        default_headers: dict of headers applied to every request
    """

    def _resolve_placeholders(self, value: str) -> str:
        """Replace {config.KEY} placeholders with config values."""
        config = self.suite_config.config
        return _PLACEHOLDER_RE.sub(
            lambda m: str(config.get(m.group(1), m.group(0))),
            value,
        )

    def _build_url(self, case: TestCase) -> str:
        """Build full URL from params and config."""
        params = case.params
        base_url = self.suite_config.config.get("base_url", "")
        url = params.get("url", "") or params.get("path", "")

        # Resolve {config.KEY} placeholders
        if "{config." in url:
            url = self._resolve_placeholders(url)

        # Build full URL
        if url and not url.startswith("http"):
            url = f"{base_url.rstrip('/')}/{url.lstrip('/')}"
        elif not url:
            url = base_url

        # Append query parameters
        query_params = params.get("query_params")
        if query_params and isinstance(query_params, dict):
            separator = "&" if "?" in url else "?"
            qs = urllib.parse.urlencode(query_params, quote_via=urllib.parse.quote)
            url = f"{url}{separator}{qs}"

        return url

    def _build_headers(self, case: TestCase) -> dict[str, str]:
        """Build request headers from config and params."""
        config = self.suite_config.config
        params = case.params

        # Start with config-level default_headers
        headers = dict(config.get("default_headers", {}))

        # Merge per-case headers (override defaults)
        headers.update(params.get("headers", {}))

        # Authorization
        token = config.get("token", "")
        if not params.get("no_auth") and token:
            scheme = config.get("auth_scheme", "Bearer")
            headers.setdefault("Authorization", f"{scheme} {token}")

        return headers

    def _parse_expected_status(self, case: TestCase) -> list[int]:
        """Parse expected status from params or TestCase.expected_result."""
        params = case.params

        # Check params first
        expected = params.get("expected_status")
        if isinstance(expected, list):
            return expected

        # Fall back to TestCase.expected_result ("400/422" format)
        raw = expected or case.expected_result
        if not raw:
            return [200]

        codes = []
        for part in str(raw).split("/"):
            part = part.strip()
            if part.isdigit():
                codes.append(int(part))
        return codes if codes else [200]

    def execute(self, case: TestCase, dry_run: bool = False) -> TestResult:
        params = case.params
        method = params.get("method", "GET").upper()
        url = self._build_url(case)
        headers = self._build_headers(case)
        body = params.get("body")
        expected_status = self._parse_expected_status(case)
        timeout = params.get("timeout", 10)

        if dry_run:
            return TestResult(
                test_id=case.test_id,
                status=TestStatus.SKIP,
                message="[DRY-RUN]",
                details=self.get_dry_run_info(case),
            )

        try:
            data = None
            if body is not None:
                if isinstance(body, dict):
                    data = json.dumps(body).encode("utf-8")
                    headers.setdefault("Content-Type", "application/json")
                else:
                    data = str(body).encode("utf-8")

            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status_code = resp.status
                resp_headers = dict(resp.headers)
                resp_body = resp.read().decode("utf-8", errors="replace")

            body_excerpt = resp_body[:500] if resp_body else ""
            result_status = TestStatus.OK if status_code in expected_status else TestStatus.NG
            message = f"{method} {url} -> {status_code}"
            if result_status == TestStatus.NG:
                message += f" (expected {expected_status})"

            return TestResult(
                test_id=case.test_id,
                status=result_status,
                message=message,
                details={
                    "request_method": method,
                    "request_url": url,
                    "request_headers": headers,
                    "request_body": body if isinstance(body, (dict, type(None))) else str(body)[:200],
                    "status_code": status_code,
                    "expected_status": expected_status,
                    "response_headers": resp_headers,
                    "response_body": resp_body,
                    "body_excerpt": body_excerpt,
                },
            )

        except urllib.error.HTTPError as e:
            status_code = e.code
            resp_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            result_status = TestStatus.OK if status_code in expected_status else TestStatus.NG
            message = f"{method} {url} -> {status_code}"
            if result_status == TestStatus.NG:
                message += f" (expected {expected_status})"

            return TestResult(
                test_id=case.test_id,
                status=result_status,
                message=message,
                details={
                    "request_method": method,
                    "request_url": url,
                    "status_code": status_code,
                    "expected_status": expected_status,
                    "response_body": resp_body,
                    "body_excerpt": resp_body[:500],
                },
            )

        except Exception as e:
            return TestResult(
                test_id=case.test_id,
                status=TestStatus.ERROR,
                message=f"{method} {url} -> {type(e).__name__}: {e}",
                details={
                    "request_method": method,
                    "request_url": url,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            )

    def get_dry_run_info(self, case: TestCase) -> dict[str, Any]:
        params = case.params
        url = self._build_url(case)

        return {
            "test_id": case.test_id,
            "method": params.get("method", "GET"),
            "url": url,
            "headers": params.get("headers", {}),
            "body": params.get("body"),
            "expected_status": self._parse_expected_status(case),
        }
