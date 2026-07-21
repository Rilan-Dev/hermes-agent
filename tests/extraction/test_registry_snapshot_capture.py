from __future__ import annotations

import base64
import os
import subprocess
import sys
import zlib
from pathlib import Path

import pytest


def test_capture_registry_snapshot_for_phase_one(tmp_path: Path) -> None:
    env = os.environ.copy()
    env.update(
        {
            "HERMES_HOME": str(tmp_path / "home"),
            "HERMES_ENABLE_PROJECT_PLUGINS": "0",
            "HERMES_SAFE_MODE": "0",
            "HERMES_PLUGINS_DEBUG": "0",
            "PYTHONHASHSEED": "0",
        }
    )
    result = subprocess.run(
        [sys.executable, "-m", "scripts.extraction.registry_probe"],
        check=True,
        env=env,
        text=True,
        capture_output=True,
    )
    encoded = base64.b64encode(
        zlib.compress(result.stdout.encode("utf-8"), level=9)
    ).decode("ascii")
    print("REGISTRY_SNAPSHOT_ZLIB_BASE64_BEGIN")
    for offset in range(0, len(encoded), 120):
        print(encoded[offset : offset + 120])
    print("REGISTRY_SNAPSHOT_ZLIB_BASE64_END")
    pytest.fail("registry snapshot capture completed")
