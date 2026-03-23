"""Version information and stamp utilities for generated artifacts."""

from __future__ import annotations

from datetime import datetime, timezone

# Format version for generated artifacts.
# Bump this when the schema of generated files changes.
FORMAT_VERSION = 1

# Package version (kept in sync with __init__.py and pyproject.toml)
_PACKAGE_VERSION = "0.1.0"


def get_version_info() -> dict[str, str | int]:
    """Return version information dict.

    Returns:
        Dict with package_version, format_version, and package name.

    Example:
        >>> from gospelo_test_runner.version import get_version_info
        >>> info = get_version_info()
        >>> info["package"]
        'gospelo_test_runner'
    """
    return {
        "package": "gospelo_test_runner",
        "package_version": _PACKAGE_VERSION,
        "format_version": FORMAT_VERSION,
    }


def version_stamp() -> dict[str, str | int]:
    """Return a stamp dict to embed in generated JSON artifacts.

    The stamp is stored under a ``_generated`` key in output files
    so that future versions can detect and migrate old formats.

    Returns:
        Dict with generator, version, format_version, and timestamp.

    Example output::

        {
            "generator": "gospelo_test_runner",
            "version": "0.1.0",
            "format_version": 1,
            "timestamp": "2026-03-14T16:00:00+00:00"
        }
    """
    return {
        "generator": "gospelo_test_runner",
        "version": _PACKAGE_VERSION,
        "format_version": FORMAT_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
