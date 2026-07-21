import json
from pathlib import Path

from scripts.platform_inventory.cli import main


def test_cli_writes_source_state_json(monkeypatch, tmp_path: Path) -> None:
    from scripts.platform_inventory.models import SourceState

    monkeypatch.setattr(
        "scripts.platform_inventory.cli.read_source_state",
        lambda root: SourceState(root.resolve(), "test", "a" * 40, False, {"origin": "example"}),
    )
    output = tmp_path / "generated"

    assert main(["--root", str(tmp_path), "--output", str(output), "source-state"]) == 0
    payload = json.loads((output / "source-state.json").read_text(encoding="utf-8"))
    assert payload["head_sha"] == "a" * 40
    assert payload["branch"] == "test"
