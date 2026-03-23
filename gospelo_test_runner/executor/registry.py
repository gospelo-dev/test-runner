"""Executor plugin registry using entry_points.

External packages can register executors via the
``gospelo_test_runner.executors`` entry-point group:

    # pyproject.toml of a plugin package
    [project.entry-points."gospelo_test_runner.executors"]
    boto3 = "my_plugin:Boto3Executor"

Built-in executors (http, process) are registered in this package's
own pyproject.toml so they go through the same discovery mechanism.
"""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import BaseExecutor

ENTRY_POINT_GROUP = "gospelo_test_runner.executors"


def list_executors() -> list[str]:
    """Return names of all registered executors."""
    eps = entry_points(group=ENTRY_POINT_GROUP)
    return sorted(ep.name for ep in eps)


def get_executor_class(name: str) -> type[BaseExecutor]:
    """Load an executor class by its registered name.

    Raises:
        KeyError: If no executor is registered under *name*.
    """
    eps = entry_points(group=ENTRY_POINT_GROUP)
    for ep in eps:
        if ep.name == name:
            cls = ep.load()
            return cls
    available = list_executors()
    msg = f"Unknown executor: {name!r}. Available: {available}"
    raise KeyError(msg)
