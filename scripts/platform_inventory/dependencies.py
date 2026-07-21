from __future__ import annotations

import json
import tomllib
from pathlib import Path

from .models import DependencyMap, InventoryError

_JS_PACKAGE_PATHS = (
    Path("web/package.json"),
    Path("apps/desktop/package.json"),
    Path("apps/shared/package.json"),
)
_TEST_SUFFIXES = (
    ".test.ts",
    ".test.tsx",
    ".test.js",
    ".test.jsx",
    ".spec.ts",
    ".spec.tsx",
    ".spec.js",
    ".spec.jsx",
)


def _read_pyproject(repository: Path) -> tuple[tuple[str, ...], dict[str, tuple[str, ...]]]:
    path = repository / "pyproject.toml"
    if not path.exists():
        raise InventoryError(f"{path}: missing pyproject.toml")
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise InventoryError(f"{path}: invalid TOML") from exc
    project = payload.get("project", {})
    if not isinstance(project, dict):
        raise InventoryError(f"{path}: [project] must be a table")
    dependencies = project.get("dependencies", [])
    if not isinstance(dependencies, list) or not all(
        isinstance(item, str) for item in dependencies
    ):
        raise InventoryError(f"{path}: project.dependencies must be a string array")
    extras_payload = project.get("optional-dependencies", {})
    if not isinstance(extras_payload, dict):
        raise InventoryError(f"{path}: project.optional-dependencies must be a table")
    extras: dict[str, tuple[str, ...]] = {}
    for name, values in sorted(extras_payload.items()):
        if not isinstance(name, str) or not isinstance(values, list) or not all(
            isinstance(item, str) for item in values
        ):
            raise InventoryError(
                f"{path}: optional dependency groups must map to string arrays"
            )
        extras[name] = tuple(sorted(set(values)))
    return tuple(sorted(set(dependencies))), extras


def _javascript_packages(repository: Path) -> dict[str, tuple[str, ...]]:
    result: dict[str, tuple[str, ...]] = {}
    for relative in _JS_PACKAGE_PATHS:
        path = repository / relative
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise InventoryError(f"{path}: invalid package.json") from exc
        if not isinstance(payload, dict):
            raise InventoryError(f"{path}: package.json must be an object")
        names: set[str] = set()
        for field in ("dependencies", "devDependencies", "optionalDependencies"):
            values = payload.get(field, {})
            if values is None:
                continue
            if not isinstance(values, dict):
                raise InventoryError(f"{path}: {field} must be an object")
            names.update(str(name) for name in values)
        result[relative.parent.as_posix()] = tuple(sorted(names))
    return dict(sorted(result.items()))


def _python_tests(repository: Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    root = repository / "tests"
    if not root.exists():
        return result
    for path in sorted(root.rglob("test_*.py")):
        relative_to_tests = path.relative_to(root)
        area = relative_to_tests.parts[0] if len(relative_to_tests.parts) > 1 else "root"
        result.setdefault(area, []).append(path.relative_to(repository).as_posix())
    return result


def _javascript_tests(repository: Path, result: dict[str, list[str]]) -> None:
    for relative, area in (
        (Path("web"), "web"),
        (Path("apps/desktop"), "desktop"),
        (Path("apps/shared"), "shared"),
    ):
        base = repository / relative
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or not path.name.endswith(_TEST_SUFFIXES):
                continue
            result.setdefault(area, []).append(path.relative_to(repository).as_posix())


def scan_dependencies(root: Path) -> DependencyMap:
    repository = root.resolve()
    python_core, python_extras = _read_pyproject(repository)
    tests = _python_tests(repository)
    _javascript_tests(repository, tests)
    return DependencyMap(
        python_core=python_core,
        python_extras=python_extras,
        javascript_packages=_javascript_packages(repository),
        tests_by_area={
            area: tuple(sorted(set(paths))) for area, paths in sorted(tests.items())
        },
    )
