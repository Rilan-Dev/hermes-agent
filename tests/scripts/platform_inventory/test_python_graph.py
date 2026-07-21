from pathlib import Path

import pytest

from scripts.platform_inventory.models import InventoryError
from scripts.platform_inventory.python_graph import scan_python_graph


def test_scan_python_graph_resolves_absolute_and_dynamic_imports(tmp_path: Path) -> None:
    package = tmp_path / "gateway"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "base.py").write_text("VALUE = 1\n", encoding="utf-8")
    (package / "run.py").write_text(
        "from gateway.base import VALUE\n"
        "import importlib\n"
        "importlib.import_module('gateway.base')\n",
        encoding="utf-8",
    )

    graph = scan_python_graph(tmp_path, [Path("gateway")])

    assert [record.path for record in graph.files] == [
        "gateway/__init__.py",
        "gateway/base.py",
        "gateway/run.py",
    ]
    assert any(
        edge.source == "gateway/run.py" and edge.target == "gateway/base.py"
        for edge in graph.imports
    )
    assert graph.dynamic_imports == ("gateway/run.py:gateway.base",)
    assert graph.unresolved_local_imports == ()
    assert all(len(record.sha256) == 64 for record in graph.files)


def test_scan_python_graph_resolves_relative_and_from_package_imports(tmp_path: Path) -> None:
    package = tmp_path / "providers"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "base.py").write_text("class Provider: pass\n", encoding="utf-8")
    (package / "registry.py").write_text(
        "from .base import Provider\nfrom providers import base\n",
        encoding="utf-8",
    )

    graph = scan_python_graph(tmp_path, [Path("providers")])

    registry_edges = [edge for edge in graph.imports if edge.source == "providers/registry.py"]
    assert [edge.target for edge in registry_edges] == ["providers/base.py", "providers/base.py"]
    assert graph.unresolved_local_imports == ()


def test_scan_python_graph_reports_missing_local_module(tmp_path: Path) -> None:
    package = tmp_path / "gateway"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "run.py").write_text("from gateway.missing import value\n", encoding="utf-8")

    graph = scan_python_graph(tmp_path, [Path("gateway")])

    assert graph.unresolved_local_imports == ("gateway/run.py:gateway.missing",)


def test_scan_python_graph_reports_importerror_guarded_local_import_as_optional(
    tmp_path: Path,
) -> None:
    agent = tmp_path / "agent"
    tui = tmp_path / "tui_gateway"
    agent.mkdir()
    tui.mkdir()
    (agent / "__init__.py").write_text("", encoding="utf-8")
    (tui / "__init__.py").write_text("", encoding="utf-8")
    (tui / "render.py").write_text(
        "try:\n"
        "    from agent.rich_output import format_response\n"
        "except ImportError:\n"
        "    format_response = None\n",
        encoding="utf-8",
    )

    graph = scan_python_graph(tmp_path, [Path("agent"), Path("tui_gateway")])

    assert graph.unresolved_local_imports == ()
    assert graph.optional_local_imports == (
        "tui_gateway/render.py:agent.rich_output",
    )


def test_scan_python_graph_keeps_non_importerror_guarded_import_blocking(
    tmp_path: Path,
) -> None:
    agent = tmp_path / "agent"
    agent.mkdir()
    (agent / "__init__.py").write_text("", encoding="utf-8")
    (agent / "consumer.py").write_text(
        "try:\n"
        "    from agent.missing import value\n"
        "except ValueError:\n"
        "    value = None\n",
        encoding="utf-8",
    )

    graph = scan_python_graph(tmp_path, [Path("agent")])

    assert graph.unresolved_local_imports == (
        "agent/consumer.py:agent.missing",
    )
    assert graph.optional_local_imports == ()


def test_scan_python_graph_wraps_syntax_errors(tmp_path: Path) -> None:
    path = tmp_path / "gateway.py"
    path.write_text("def broken(:\n", encoding="utf-8")

    with pytest.raises(InventoryError, match="gateway.py: invalid Python syntax"):
        scan_python_graph(tmp_path, [Path("gateway.py")])
