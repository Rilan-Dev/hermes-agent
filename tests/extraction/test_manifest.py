from pathlib import Path

import pytest

from scripts.extraction.manifest import ManifestError, load_manifest
from scripts.extraction.schema import Classification


def test_repository_manifest_loads() -> None:
    manifest = load_manifest(
        Path("extracted/hermes-connect-kit/extraction-manifest.yaml")
    )
    assert manifest.version == 1
    assert manifest.source_sha == "d7b36070ef807841699ad32c5b6af547fee3ff64"
    assert {rule.path for rule in manifest.dynamic_roots} >= {
        "plugins/platforms",
        "plugins/model-providers",
        "providers",
        "gateway/relay",
        "gateway/platforms",
    }
    assert manifest.dynamic_roots[0].classification is Classification.CORE


@pytest.mark.parametrize("value", ["", "/absolute", "../escape", "a/../../escape"])
def test_manifest_rejects_unsafe_paths(tmp_path: Path, value: str) -> None:
    path = tmp_path / "manifest.yaml"
    path.write_text(
        f"""version: 1
source_repository: Rilan-Dev/hermes-agent
source_sha: d7b36070ef807841699ad32c5b6af547fee3ff64
dynamic_roots:
  - path: {value!r}
    classification: core
    destination: vendor/root
    reason: invalid
explicit_files: []
test_rules: []
internal_module_roots: []
""",
        encoding="utf-8",
    )
    with pytest.raises(ManifestError):
        load_manifest(path)
