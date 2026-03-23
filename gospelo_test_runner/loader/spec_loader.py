"""Test spec loaders (JSON and YAML)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..types import TestCase


def load_spec_yml(spec_path: str | Path) -> tuple[str, str, dict[str, list[TestCase]]]:
    """Load test spec YAML and convert to TestCase groups.

    All YAML fields (except ``test_id``, ``category``, ``description``,
    ``name``) are passed through to ``TestCase.params`` as-is.  This
    allows a single loader to handle HTTP tests, header-inspection tests,
    infrastructure tests, load tests, and any future test type.

    HTTP-specific backward-compatible transformations are applied only
    when the YAML contains HTTP-like fields (``endpoint``, ``params``).

    Minimal required YAML structure::

        suite_name: "..."
        test_cases:
          - test_id: "XX-01"
            category: "..."
            description: "..."
            # ... any additional fields become params

    Args:
        spec_path: Path to the YAML spec file.

    Returns:
        Tuple of (suite_name, test_id_prefix, {category: [TestCase, ...]})
    """
    import yaml

    path = Path(spec_path)
    if not path.exists():
        raise FileNotFoundError(f"Spec file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    suite_name = data.get("suite_name", "")
    base_url = data.get("base_url", "")
    # Derive test_id_prefix from first test_id (e.g., "SI-SQL-01" -> "SI")
    test_cases_raw = data.get("test_cases", [])
    test_id_prefix = ""
    if test_cases_raw:
        first_id = test_cases_raw[0].get("test_id", "")
        if "-" in first_id:
            test_id_prefix = first_id.split("-")[0]

    # Fields that map to TestCase attributes (excluded from params)
    _attr_fields = {"test_id", "category", "description", "name"}

    groups: dict[str, list[TestCase]] = {}
    for tc_data in test_cases_raw:
        category = tc_data.get("category", "")

        # Build expected_result string for display
        expected_status = tc_data.get("expected_status", "")
        expected_body = tc_data.get("expected_body_contains", [])
        expected_parts = []
        if expected_status:
            expected_parts.append(f"status={expected_status}")
        if expected_body:
            expected_parts.append(f"body contains {expected_body}")

        # Pass through ALL YAML fields to params (except TestCase attributes)
        params = {k: v for k, v in tc_data.items() if k not in _attr_fields}

        # HTTP-compatible transformations (backward compatibility)
        # Only rename endpoint→url when it looks like a real HTTP path
        endpoint = params.get("endpoint")
        if endpoint and endpoint != "-":
            params["url"] = params.pop("endpoint")
        if "params" in params and isinstance(params["params"], dict):
            params["query_params"] = params.pop("params")
        if base_url:
            params["base_url"] = base_url

        # Normalize expected_status to list[int]
        if isinstance(expected_status, int):
            params["expected_status"] = [expected_status]

        tc = TestCase(
            test_id=tc_data.get("test_id", ""),
            category=category,
            description=tc_data.get("description", tc_data.get("name", "")),
            test_type=tc_data.get("test_type", tc_data.get("method", "")),
            expected_result=" / ".join(expected_parts) if expected_parts else "",
            params=params,
        )
        groups.setdefault(category, []).append(tc)

    return suite_name, test_id_prefix, groups


def load_spec_json(spec_path: str | Path) -> tuple[str, str, dict[str, list[TestCase]]]:
    """Load test spec JSON and convert to TestCase groups.

    Args:
        spec_path: Path to the test_spec.json file.

    Returns:
        Tuple of (test_name, test_id_prefix, {category: [TestCase, ...]})

    Raises:
        FileNotFoundError: If spec file does not exist.
    """
    path = Path(spec_path)
    if not path.exists():
        raise FileNotFoundError(f"Spec file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    test_name = data.get("test_name", "")
    test_id_prefix = data.get("test_id_prefix", "")

    groups: dict[str, list[TestCase]] = {}
    for case_data in data.get("cases", []):
        group = case_data.get("group", "")
        tc = TestCase(
            test_id=case_data.get("id", ""),
            category=group,
            description=case_data.get("input", ""),
            test_type=case_data.get("method", ""),
            expected_result=case_data.get("expected", ""),
            params={
                "api": case_data.get("api", ""),
                "param": case_data.get("param", ""),
                "script_cmd": case_data.get("script_cmd", ""),
            },
        )
        groups.setdefault(group, []).append(tc)

    return test_name, test_id_prefix, groups


def load_prereq_json(prereq_path: str | Path | None) -> dict[str, Any] | None:
    """Load prerequisites JSON for Excel generation.

    Args:
        prereq_path: Path to test_prereq.json, or None.

    Returns:
        Parsed prereq dict, or None if path is None or file doesn't exist.
    """
    if prereq_path is None:
        return None

    path = Path(prereq_path)
    if not path.exists():
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
