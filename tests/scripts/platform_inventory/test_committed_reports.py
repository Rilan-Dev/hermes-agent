from __future__ import annotations

import json
from pathlib import Path

import yaml


REPORT_ROOT = Path("generated/platform_inventory")
REPORT_NAMES = {
    "channel-capabilities.md",
    "dependency-test-map.md",
    "extraction-manifest.yaml",
    "frontend-api-map.md",
    "inventory.json",
    "phase-0-review.md",
    "provider-capabilities.md",
    "source-state.json",
    "tool-capabilities.md",
}


def test_committed_phase0_reports_are_complete_and_self_consistent() -> None:
    assert REPORT_ROOT.is_dir(), "validated Phase 0 reports must be committed"
    assert {path.name for path in REPORT_ROOT.iterdir() if path.is_file()} == REPORT_NAMES

    inventory = json.loads((REPORT_ROOT / "inventory.json").read_text(encoding="utf-8"))
    source = json.loads((REPORT_ROOT / "source-state.json").read_text(encoding="utf-8"))
    manifest = yaml.safe_load(
        (REPORT_ROOT / "extraction-manifest.yaml").read_text(encoding="utf-8")
    )
    review = (REPORT_ROOT / "phase-0-review.md").read_text(encoding="utf-8")

    assert inventory["schema_version"] == manifest["version"] == 1
    assert inventory["source"] == source
    assert manifest["source"]["sha"] == source["head_sha"]
    assert len(source["head_sha"]) == 40
    assert source["dirty"] is False
    assert inventory["plugins"]
    assert inventory["registries"]["platforms"]
    assert inventory["registries"]["canonical_providers"]
    assert inventory["registries"]["tools"]
    assert inventory["frontend"]["routes"]
    assert inventory["python_graph"]["unresolved_local_imports"] == []
    assert inventory["registries"]["probe_errors"] == []
    assert manifest["unresolved_imports"] == []
    assert manifest["runtime_probe_errors"] == []
    assert manifest["optional_imports"] == inventory["python_graph"][
        "optional_local_imports"
    ]
    assert "**Status:** READY FOR REVIEW" in review
    assert "- None" in review
