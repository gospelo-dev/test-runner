"""Log reporter - captures stdout to evidence log files."""

from __future__ import annotations

import sys
from datetime import datetime
from io import TextIOWrapper
from pathlib import Path
from typing import TextIO


class TeeWriter:
    """Write to both stdout and a log file simultaneously."""

    def __init__(self, original: TextIO, log_file: TextIOWrapper) -> None:
        self.original = original
        self.log_file = log_file

    def write(self, text: str) -> int:
        self.original.write(text)
        self.log_file.write(text)
        return len(text)

    def flush(self) -> None:
        self.original.flush()
        self.log_file.flush()


class LogReporter:
    """Manage evidence log file creation and stdout capture.

    Usage:
        reporter = LogReporter("logs")
        reporter.start()
        # ... all print() output is captured ...
        reporter.stop()
        print(f"Log saved to: {reporter.log_path}")
    """

    def __init__(self, output_dir: str | Path, evidence_name: str = "") -> None:
        self.output_dir = Path(output_dir)
        self.evidence_name = evidence_name
        self.log_path: Path | None = None
        self._log_file: TextIOWrapper | None = None
        self._original_stdout: TextIO | None = None

    def start(self) -> Path:
        """Start capturing stdout to a log file.

        Returns:
            Path to the log file being written.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if self.evidence_name:
            self.log_path = self.output_dir / f"{self.evidence_name}.log"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.log_path = self.output_dir / f"evidence_{timestamp}.log"

        self._log_file = open(self.log_path, "w", encoding="utf-8")
        self._original_stdout = sys.stdout
        sys.stdout = TeeWriter(self._original_stdout, self._log_file)  # type: ignore[assignment]

        return self.log_path

    def stop(self) -> None:
        """Stop capturing and restore original stdout."""
        if self._original_stdout is not None:
            sys.stdout = self._original_stdout
            self._original_stdout = None

        if self._log_file is not None:
            self._log_file.close()
            self._log_file = None
