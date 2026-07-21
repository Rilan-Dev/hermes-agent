from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from .source_state import read_source_state


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


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    state = read_source_state(args.root)
    if args.command == "source-state":
        _write_json(args.output / "source-state.json", state.to_dict())
        return 0
    raise SystemExit("generate is added in Task 7")
