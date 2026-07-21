from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Classification(str, Enum):
    CORE = "core"
    HOST_PORT = "host_port"
    OPTIONAL_UI = "optional_ui"
    TEST = "test"
    EXCLUDE_BY_DEFAULT = "exclude_by_default"


@dataclass(frozen=True)
class RootRule:
    path: str
    classification: Classification
    destination: str
    reason: str


@dataclass(frozen=True)
class FileRule:
    path: str
    classification: Classification
    destination: str
    reason: str


@dataclass(frozen=True)
class TestRule:
    path: str
    kind: str
    behavior: str


@dataclass(frozen=True)
class ExtractionManifest:
    version: int
    source_repository: str
    source_sha: str
    dynamic_roots: tuple[RootRule, ...]
    explicit_files: tuple[FileRule, ...]
    test_rules: tuple[TestRule, ...]
    internal_module_roots: tuple[str, ...]
