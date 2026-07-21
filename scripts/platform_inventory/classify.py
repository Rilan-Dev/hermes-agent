from __future__ import annotations

from pathlib import PurePosixPath


def classify_path(path: str) -> str:
    p = PurePosixPath(path)
    if path.startswith("tests/"):
        return "test"
    if path.startswith("apps/desktop/") or path.startswith("web/"):
        return "frontend"
    if path.startswith("plugins/platforms/") or path.startswith(
        "plugins/model-providers/"
    ):
        return "core-plugin"
    if path.startswith("gateway/") or path.startswith("providers/"):
        return "core"
    if path.startswith("tools/") or p.name in {
        "toolsets.py",
        "toolset_distributions.py",
    }:
        return "tool-runtime"
    if path.startswith("hermes_cli/") or path.startswith("agent/"):
        return "host-runtime"
    return "support"
