from __future__ import annotations

import ast
import hashlib
import importlib.util
from pathlib import Path
from typing import Sequence

from .classify import classify_path
from .models import FileRecord, ImportEdge, InventoryError, PythonGraph


def _module_name(relative: Path) -> str:
    parts = list(relative.with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _module_index(root: Path) -> dict[str, str]:
    index: dict[str, str] = {}
    for path in sorted(root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(root)
        module = _module_name(relative)
        if module:
            index[module] = relative.as_posix()
    return index


def _source_package(relative: Path) -> str:
    module = _module_name(relative)
    if relative.name == "__init__.py":
        return module
    return module.rpartition(".")[0]


def _resolve(module: str, index: dict[str, str]) -> str | None:
    return index.get(module)


def _from_base(node: ast.ImportFrom, package: str) -> str:
    if node.level:
        relative_name = "." * node.level + (node.module or "")
        try:
            return importlib.util.resolve_name(relative_name, package)
        except (ImportError, ValueError):
            return node.module or ""
    return node.module or ""


def _catches_import_error(handler: ast.ExceptHandler) -> bool:
    exception = handler.type
    if exception is None:
        return True
    candidates = exception.elts if isinstance(exception, ast.Tuple) else (exception,)
    for candidate in candidates:
        if isinstance(candidate, ast.Name) and candidate.id in {
            "ImportError",
            "ModuleNotFoundError",
        }:
            return True
        if (
            isinstance(candidate, ast.Attribute)
            and candidate.attr in {"ImportError", "ModuleNotFoundError"}
        ):
            return True
    return False


class _OptionalImportCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.optional_nodes: set[int] = set()
        self._guard_depth = 0

    def visit_Try(self, node: ast.Try) -> None:
        guarded = any(_catches_import_error(handler) for handler in node.handlers)
        if guarded:
            self._guard_depth += 1
        for statement in node.body:
            self.visit(statement)
        if guarded:
            self._guard_depth -= 1
        for handler in node.handlers:
            for statement in handler.body:
                self.visit(statement)
        for statement in node.orelse:
            self.visit(statement)
        for statement in node.finalbody:
            self.visit(statement)

    def visit_Import(self, node: ast.Import) -> None:
        if self._guard_depth:
            self.optional_nodes.add(id(node))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if self._guard_depth:
            self.optional_nodes.add(id(node))

    def _visit_deferred_body(self, node: ast.AST) -> None:
        previous = self._guard_depth
        self._guard_depth = 0
        self.generic_visit(node)
        self._guard_depth = previous

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_deferred_body(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_deferred_body(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._visit_deferred_body(node)


def _optional_import_nodes(tree: ast.AST) -> set[int]:
    collector = _OptionalImportCollector()
    collector.visit(tree)
    return collector.optional_nodes


def _selected_files(root: Path, include_paths: Sequence[Path]) -> set[Path]:
    selected: set[Path] = set()
    for relative in include_paths:
        absolute = root / relative
        if absolute.is_file() and absolute.suffix == ".py":
            selected.add(absolute)
        elif absolute.is_dir():
            selected.update(
                path
                for path in absolute.rglob("*.py")
                if path.is_file() and "__pycache__" not in path.parts
            )
    return selected


def scan_python_graph(root: Path, include_paths: Sequence[Path]) -> PythonGraph:
    repository = root.resolve()
    index = _module_index(repository)
    local_prefixes = {module.split(".", 1)[0] for module in index}

    files: list[FileRecord] = []
    imports: list[ImportEdge] = []
    dynamic: set[str] = set()
    unresolved: set[str] = set()
    optional_unresolved: set[str] = set()

    for path in sorted(_selected_files(repository, include_paths)):
        relative_path = path.relative_to(repository)
        relative = relative_path.as_posix()
        content = path.read_bytes()
        files.append(
            FileRecord(
                path=relative,
                sha256=hashlib.sha256(content).hexdigest(),
                size_bytes=len(content),
                classification=classify_path(relative),
            )
        )
        try:
            tree = ast.parse(content.decode("utf-8"), filename=relative)
        except (SyntaxError, UnicodeDecodeError) as exc:
            raise InventoryError(f"{relative}: invalid Python syntax or encoding") from exc

        package = _source_package(relative_path)
        optional_nodes = _optional_import_nodes(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    target = _resolve(alias.name, index)
                    imports.append(ImportEdge(relative, alias.name, target))
                    if target is None and alias.name.split(".", 1)[0] in local_prefixes:
                        collection = (
                            optional_unresolved
                            if id(node) in optional_nodes
                            else unresolved
                        )
                        collection.add(f"{relative}:{alias.name}")
            elif isinstance(node, ast.ImportFrom):
                base = _from_base(node, package)
                for alias in node.names:
                    if alias.name == "*":
                        module = base
                        target = _resolve(base, index) if base else None
                    else:
                        full = f"{base}.{alias.name}" if base else alias.name
                        full_target = _resolve(full, index)
                        base_target = _resolve(base, index) if base else None
                        if full_target is not None:
                            module, target = full, full_target
                        elif base_target is not None:
                            module, target = base, base_target
                        else:
                            module, target = (base or full), None
                    imports.append(ImportEdge(relative, module, target))
                    root_name = module.split(".", 1)[0] if module else ""
                    if target is None and root_name in local_prefixes:
                        collection = (
                            optional_unresolved
                            if id(node) in optional_nodes
                            else unresolved
                        )
                        collection.add(f"{relative}:{module}")
            elif isinstance(node, ast.Call):
                value: str | None = None
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "import_module"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                ):
                    value = node.args[0].value
                elif (
                    isinstance(node.func, ast.Name)
                    and node.func.id in {"import_module", "__import__"}
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)
                ):
                    value = node.args[0].value
                if value:
                    dynamic.add(f"{relative}:{value}")

    return PythonGraph(
        files=tuple(sorted(files, key=lambda record: record.path)),
        imports=tuple(
            sorted(imports, key=lambda edge: (edge.source, edge.module, edge.target or ""))
        ),
        dynamic_imports=tuple(sorted(dynamic)),
        unresolved_local_imports=tuple(sorted(unresolved)),
        optional_local_imports=tuple(sorted(optional_unresolved)),
    )
