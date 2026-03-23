"""JSON evidence reporter - outputs structured test results as JSON."""

from __future__ import annotations

import json
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from ..types import TestResult, TestSuiteMeta, TestStatus
from ..version import version_stamp


class JsonReporter:
    """Generate evidence JSON files from test results.

    Output format:
        {
            "meta": { test_name, timestamp, executor, region, environment, summary },
            "results": [ { test_id, status, message, details, evidence } ]
        }
    """

    def __init__(self, output_dir: str | Path, test_name: str = "", evidence_name: str = "") -> None:
        self.output_dir = Path(output_dir)
        self.test_name = test_name
        self.evidence_name = evidence_name

    def write(
        self,
        results: list[TestResult],
        executor: str = "",
        region: str = "",
        max_detail_responses: int = 5,
    ) -> Path:
        """Write test results to a JSON evidence file.

        Args:
            results: List of TestResult objects.
            executor: Executor name for metadata.
            region: Region or environment identifier.
            max_detail_responses: Max number of response entries to keep per result.

        Returns:
            Path to the written JSON file.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if self.evidence_name:
            output_path = self.output_dir / f"{self.evidence_name}.json"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"evidence_{timestamp}.json"

        summary = self._compute_summary(results)
        meta = TestSuiteMeta(
            test_name=self.test_name,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            executor=executor,
            region=region,
            environment={
                "python": sys.version,
                "platform": platform.platform(),
                "docker": self._detect_docker(),
            },
            summary=summary,
        )

        serialized_results = []
        for r in results:
            entry = self._serialize_result(r, max_detail_responses)
            serialized_results.append(entry)

        output = {
            "_generated": version_stamp(),
            "meta": {
                "test_name": meta.test_name,
                "timestamp": meta.timestamp,
                "executor": meta.executor,
                "region": meta.region,
                "environment": meta.environment,
                "summary": meta.summary,
            },
            "results": serialized_results,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        return output_path

    def _serialize_result(
        self, result: TestResult, max_responses: int
    ) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "test_id": result.test_id,
            "status": result.status.value,
            "message": result.message,
        }

        details = dict(result.details)
        responses = details.get("responses")
        if isinstance(responses, list) and len(responses) > max_responses:
            details["responses"] = responses[-max_responses:]
            details["responses_truncated"] = True

        entry["details"] = details

        if result.evidence:
            entry["evidence"] = result.evidence

        return entry

    @staticmethod
    def _compute_summary(results: list[TestResult]) -> dict[str, int]:
        summary: dict[str, int] = {"total": len(results), "ok": 0, "ng": 0, "error": 0, "info": 0, "skip": 0}
        for r in results:
            key = r.status.value.lower()
            if key in summary:
                summary[key] += 1
        return summary

    @staticmethod
    def _detect_docker() -> str:
        try:
            return str(Path("/.dockerenv").exists())
        except Exception:
            return "unknown"
