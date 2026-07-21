from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from scripts.extraction.schema import (
    Classification,
    ExtractionManifest,
    FileRule,
    RootRule,
    TestRule,
)

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_TEST_RULE_KINDS = frozenset({"root", "file", "glob"})


class ManifestError(ValueError):
    pass


def _safe_repo_path(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{field} must be a non-empty string")
    text = value.strip().replace("\\", "/")
    path = PurePosixPath(text)
    if path.is_absolute() or ".." in path.parts or text == ".":
        raise ManifestError(f"{field} must be repository-relative")
    return path.as_posix()


def _mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ManifestError(f"{field} must be a mapping")
    return value


def _sequence(value: object, field: str) -> Sequence[object]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ManifestError(f"{field} must be a list")
    return value


def _required_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{field} must be a non-empty string")
    return value.strip()


def _classification(value: object, field: str) -> Classification:
    text = _required_text(value, field)
    try:
        return Classification(text)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in Classification)
        raise ManifestError(f"{field} must be one of: {allowed}") from exc


def _root_rule(value: object, index: int) -> RootRule:
    item = _mapping(value, f"dynamic_roots[{index}]")
    prefix = f"dynamic_roots[{index}]"
    return RootRule(
        path=_safe_repo_path(item.get("path"), f"{prefix}.path"),
        classification=_classification(
            item.get("classification"), f"{prefix}.classification"
        ),
        destination=_safe_repo_path(
            item.get("destination"), f"{prefix}.destination"
        ),
        reason=_required_text(item.get("reason"), f"{prefix}.reason"),
    )


def _file_rule(value: object, index: int) -> FileRule:
    item = _mapping(value, f"explicit_files[{index}]")
    prefix = f"explicit_files[{index}]"
    return FileRule(
        path=_safe_repo_path(item.get("path"), f"{prefix}.path"),
        classification=_classification(
            item.get("classification"), f"{prefix}.classification"
        ),
        destination=_safe_repo_path(
            item.get("destination"), f"{prefix}.destination"
        ),
        reason=_required_text(item.get("reason"), f"{prefix}.reason"),
    )


def _test_rule(value: object, index: int) -> TestRule:
    item = _mapping(value, f"test_rules[{index}]")
    prefix = f"test_rules[{index}]"
    kind = _required_text(item.get("kind"), f"{prefix}.kind")
    if kind not in _TEST_RULE_KINDS:
        allowed = ", ".join(sorted(_TEST_RULE_KINDS))
        raise ManifestError(f"{prefix}.kind must be one of: {allowed}")
    return TestRule(
        path=_safe_repo_path(item.get("path"), f"{prefix}.path"),
        kind=kind,
        behavior=_required_text(item.get("behavior"), f"{prefix}.behavior"),
    )


def load_manifest(path: Path) -> ExtractionManifest:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ManifestError(f"unable to read manifest {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ManifestError(f"invalid YAML in manifest {path}: {exc}") from exc

    data = _mapping(raw, "manifest")
    version = data.get("version")
    if version != 1:
        raise ManifestError("version must be 1")

    source_repository = _required_text(
        data.get("source_repository"), "source_repository"
    )
    source_sha = _required_text(data.get("source_sha"), "source_sha")
    if _SHA_RE.fullmatch(source_sha) is None:
        raise ManifestError("source_sha must be a lowercase 40-character Git SHA")

    dynamic_roots = tuple(
        _root_rule(value, index)
        for index, value in enumerate(
            _sequence(data.get("dynamic_roots"), "dynamic_roots")
        )
    )
    explicit_files = tuple(
        _file_rule(value, index)
        for index, value in enumerate(
            _sequence(data.get("explicit_files"), "explicit_files")
        )
    )
    test_rules = tuple(
        _test_rule(value, index)
        for index, value in enumerate(
            _sequence(data.get("test_rules"), "test_rules")
        )
    )
    internal_module_roots = tuple(
        _safe_repo_path(value, f"internal_module_roots[{index}]")
        for index, value in enumerate(
            _sequence(data.get("internal_module_roots"), "internal_module_roots")
        )
    )

    return ExtractionManifest(
        version=version,
        source_repository=source_repository,
        source_sha=source_sha,
        dynamic_roots=dynamic_roots,
        explicit_files=explicit_files,
        test_rules=test_rules,
        internal_module_roots=internal_module_roots,
    )
