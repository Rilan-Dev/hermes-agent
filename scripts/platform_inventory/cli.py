from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from . import SCHEMA_VERSION
from .dependencies import scan_dependencies
from .frontend_map import scan_frontend
from .manifests import discover_plugins
from .models import InventoryReport
from .python_graph import scan_python_graph
from .reports import blocking_findings, write_reports
from .runtime_probe import probe_runtime
from .source_state import read_source_state

_PLUGIN_ROOTS = (Path("plugins"),)
_PYTHON_ROOTS = (
    Path("agent"),
    Path("gateway"),
    Path("providers"),
    Path("plugins"),
    Path("hermes_cli"),
    Path("tools"),
    Path("cron"),
    Path("tui_gateway"),
    Path("toolsets.py"),
    Path("toolset_distributions.py"),
    Path("model_tools.py"),
    Path("run_agent.py"),
    Path("hermes_state.py"),
    Path("mcp_serve.py"),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="platform-inventory")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("generated/platform_inventory"))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("source-state")
    subparsers.add_parser("generate")
    return parser


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_inventory(root: Path) -> InventoryReport:
    repository = root.resolve()
    return InventoryReport(
        schema_version=SCHEMA_VERSION,
        source=read_source_state(repository),
        plugins=tuple(discover_plugins(repository, _PLUGIN_ROOTS)),
        python_graph=scan_python_graph(repository, _PYTHON_ROOTS),
        registries=probe_runtime(repository),
        frontend=scan_frontend(repository),
        dependencies=scan_dependencies(repository),
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "source-state":
        state = read_source_state(args.root)
        _write_json(args.output / "source-state.json", state.to_dict())
        return 0
    report = build_inventory(args.root)
    write_reports(report, args.output)
    return 2 if blocking_findings(report) else 0
