from pathlib import Path

from scripts.extraction.filesystem_inventory import FileRecord
from scripts.extraction.import_inventory import inventory_imports


def record(source: str) -> FileRecord:
    return FileRecord(
        source=source,
        destination=f"vendor/{source}",
        classification="core",
        reason="test fixture",
        sha256="0" * 64,
        size_bytes=0,
    )


def test_imports_are_classified(tmp_path: Path) -> None:
    (tmp_path / "gateway").mkdir()
    (tmp_path / "gateway/__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "gateway/session.py").write_text(
        "from gateway.delivery import deliver\n"
        "from hermes_state import SessionDB\n"
        "import json\n",
        encoding="utf-8",
    )
    (tmp_path / "gateway/delivery.py").write_text(
        "def deliver(): pass\n", encoding="utf-8"
    )
    (tmp_path / "hermes_state.py").write_text(
        "class SessionDB: pass\n", encoding="utf-8"
    )

    result = inventory_imports(
        tmp_path,
        (record("gateway/session.py"), record("gateway/delivery.py")),
        ("gateway", "hermes_state"),
    )[1]

    assert result.source == "gateway/session.py"
    assert result.imports_in_scope == ("gateway/delivery.py",)
    assert result.imports_out_of_scope == ("hermes_state.py",)
    assert result.external_imports == ("json",)
    assert result.unresolved_internal == ()


def test_relative_imports_resolve_from_the_current_package(tmp_path: Path) -> None:
    package = tmp_path / "providers/sub"
    package.mkdir(parents=True)
    (tmp_path / "providers/__init__.py").write_text("", encoding="utf-8")
    (package / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "providers/base.py").write_text(
        "class Profile: pass\n", encoding="utf-8"
    )
    (package / "helpers.py").write_text("VALUE = 1\n", encoding="utf-8")
    (package / "module.py").write_text(
        "from ..base import Profile\nfrom .helpers import VALUE\n",
        encoding="utf-8",
    )

    result = inventory_imports(
        tmp_path,
        (
            record("providers/base.py"),
            record("providers/sub/helpers.py"),
            record("providers/sub/module.py"),
        ),
        ("providers",),
    )[-1]

    assert result.imports_in_scope == (
        "providers/base.py",
        "providers/sub/helpers.py",
    )
    assert result.unresolved_internal == ()


def test_unresolved_internal_imports_are_reported(tmp_path: Path) -> None:
    (tmp_path / "gateway").mkdir()
    (tmp_path / "gateway/__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "gateway/session.py").write_text(
        "from gateway.missing import value\n", encoding="utf-8"
    )

    result = inventory_imports(
        tmp_path,
        (record("gateway/session.py"),),
        ("gateway",),
    )[0]

    assert result.unresolved_internal == ("gateway.missing",)
    assert result.external_imports == ()
