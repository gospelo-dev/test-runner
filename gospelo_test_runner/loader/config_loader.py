"""Configuration file loader supporting YAML and JSON formats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


def load_config(config_path: str | Path, schema: dict[str, str] | None = None) -> dict[str, Any]:
    """Load configuration from a YAML or JSON file.

    Args:
        config_path: Path to the configuration file (.yml, .yaml or .json).
        schema: Optional mapping of {flat_key: "section.key"} for extraction.
            Example: {"base_url": "api.base_url", "token": "auth.token"}
            If None, the raw parsed dict is returned.

    Returns:
        Flat dictionary of configuration values.

    Raises:
        FileNotFoundError: If config file does not exist.
        ValueError: If file format is not supported.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    if path.suffix in (".yml", ".yaml"):
        if not yaml:
            raise ImportError("pyyaml is required to load YAML config files")
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    elif path.suffix == ".json":
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
    else:
        raise ValueError(f"Unsupported config format: {path.suffix} (expected .yml or .json)")

    if schema is None:
        return raw

    result: dict[str, Any] = {}
    for flat_key, dotted_path in schema.items():
        parts = dotted_path.split(".")
        value: Any = raw
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part, "")
            else:
                value = ""
                break
        result[flat_key] = value

    return result


# Default schema for config.yml flat-key mapping.
# Maps flat keys to dotted YAML paths. Override with a custom schema dict
# when your config.yml has a different structure.
DEFAULT_CONFIG_SCHEMA: dict[str, str] = {
    "executor": "execution.executor",
    "base_url": "api.base_url",
    "service_name": "environment.service_name",
}
