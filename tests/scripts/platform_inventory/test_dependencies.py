import json
from pathlib import Path

from scripts.platform_inventory.dependencies import scan_dependencies


def test_scan_dependencies_keeps_extras_javascript_and_tests_separate(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
dependencies = ["fastapi==1.0.0", "pyyaml==6.0.3"]
[project.optional-dependencies]
messaging = ["discord.py==2.0.0"]
slack = ["slack-sdk==3.0.0"]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    web = tmp_path / "web"
    web.mkdir()
    (web / "package.json").write_text(
        json.dumps(
            {
                "dependencies": {"react": "19"},
                "devDependencies": {"vitest": "4"},
            }
        ),
        encoding="utf-8",
    )
    tests = tmp_path / "tests" / "gateway"
    tests.mkdir(parents=True)
    (tests / "test_delivery.py").write_text("def test_ok(): pass\n", encoding="utf-8")
    (web / "channels.test.tsx").write_text("test('ok', () => {});\n", encoding="utf-8")

    result = scan_dependencies(tmp_path)

    assert result.python_core == ("fastapi==1.0.0", "pyyaml==6.0.3")
    assert result.python_extras == {
        "messaging": ("discord.py==2.0.0",),
        "slack": ("slack-sdk==3.0.0",),
    }
    assert result.javascript_packages == {"web": ("react", "vitest")}
    assert result.tests_by_area == {
        "gateway": ("tests/gateway/test_delivery.py",),
        "web": ("web/channels.test.tsx",),
    }


def test_scan_dependencies_handles_missing_optional_apps(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "[project]\ndependencies = []\n",
        encoding="utf-8",
    )

    result = scan_dependencies(tmp_path)

    assert result.javascript_packages == {}
    assert result.tests_by_area == {}
