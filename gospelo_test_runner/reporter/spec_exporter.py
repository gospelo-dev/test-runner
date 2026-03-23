"""Test spec exporter - generates test_spec.json from TestCase definitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..types import TestCase
from ..version import version_stamp


def export_test_spec(
    cases: list[TestCase],
    test_name: str,
    test_id_prefix: str,
    script_prefix: str = "",
    output_dir: str | Path | None = None,
    spec_filename: str = "test_spec.json",
) -> Path:
    """Export test case definitions to a spec JSON file.

    The output JSON is consumed by report generators (e.g., generate_excel.py)
    to create test matrices and traceability documents.

    Args:
        cases: List of TestCase objects to export.
        test_name: Display name of the test suite.
        test_id_prefix: ID prefix (e.g., "03_header_injection").
        script_prefix: Script path prefix for script_cmd generation.
        output_dir: Output directory (default: current directory).
        spec_filename: Output filename (default: "test_spec.json").

    Returns:
        Path to the written spec JSON file.
    """
    spec: dict[str, Any] = {
        "_generated": version_stamp(),
        "test_name": test_name,
        "test_id_prefix": test_id_prefix,
        "cases": [],
    }

    for case in cases:
        entry: dict[str, Any] = {
            "id": case.test_id,
            "group": case.category,
            "category": case.category,
            "api": case.params.get("api", ""),
            "method": case.test_type,
            "param": _truncate(str(case.params.get("param", "")), 60),
            "input": case.description,
            "expected": case.expected_result,
            "script_cmd": (
                case.params.get("script_cmd", "")
                or f"python {script_prefix}/scripts/run_test.py"
                f" --config config.yml --test-id {case.test_id}"
            ),
        }
        spec["cases"].append(entry)

    out_dir = Path(output_dir) if output_dir else Path(".")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / spec_filename

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(spec, f, ensure_ascii=False, indent=2)

    return out_path


def _truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
