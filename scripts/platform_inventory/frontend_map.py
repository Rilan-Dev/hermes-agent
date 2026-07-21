from __future__ import annotations

import re
from pathlib import Path

from .models import FrontendMap

_SOURCE_SUFFIXES = {".ts", ".tsx", ".js", ".jsx"}
_STRING_LITERAL = re.compile(r"(?P<quote>['\"])(?P<value>(?:\\.|(?!\1).)*)\1")
_ROUTE_VALUE = re.compile(r"^/(?:[A-Za-z0-9_:-]+/?)+$")
_API_VALUE = re.compile(r"^/api/[A-Za-z0-9_./{}:-]+$")
_WS_VALUE = re.compile(r"^/ws/[A-Za-z0-9_./{}:-]+$")
_STATIC_MARKERS = (
    "MESSAGING_SESSION_SOURCE_IDS",
    "SOURCE_LABELS",
    "CANONICAL_PROVIDERS",
    "MODEL_CATALOG_TOOLSETS",
    "PLATFORM_ICONS",
    "PROVIDER_VIEWS",
    "PROVIDER_GROUPS",
)


def _strip_js_comments(text: str) -> str:
    output: list[str] = []
    index = 0
    quote: str | None = None
    escaped = False
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if quote is not None:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in {"'", '"', "`"}:
            quote = char
            output.append(char)
            index += 1
            continue
        if char == "/" and next_char == "/":
            index += 2
            while index < len(text) and text[index] not in "\r\n":
                index += 1
            continue
        if char == "/" and next_char == "*":
            index += 2
            while index + 1 < len(text) and text[index : index + 2] != "*/":
                index += 1
            index += 2 if index + 1 <= len(text) else 0
            continue
        output.append(char)
        index += 1
    return "".join(output)


def _source_files(repository: Path) -> list[Path]:
    files: set[Path] = set()
    for relative in (Path("web/src"), Path("apps/desktop/src"), Path("apps/shared")):
        base = repository / relative
        if not base.exists():
            continue
        files.update(
            path
            for path in base.rglob("*")
            if path.is_file() and path.suffix in _SOURCE_SUFFIXES
        )
    return sorted(files)


def scan_frontend(root: Path) -> FrontendMap:
    repository = root.resolve()
    routes: set[str] = set()
    api_paths: set[str] = set()
    websocket_paths: set[str] = set()
    electron: set[str] = set()
    static: set[str] = set()

    for path in _source_files(repository):
        relative = path.relative_to(repository).as_posix()
        text = _strip_js_comments(path.read_text(encoding="utf-8"))
        if "hermesDesktop" in text:
            electron.add(f"{relative}:hermesDesktop")
        for marker in _STATIC_MARKERS:
            if marker in text:
                static.add(f"{relative}:{marker}")
        for match in _STRING_LITERAL.finditer(text):
            value = bytes(match.group("value"), "utf-8").decode(
                "unicode_escape", errors="replace"
            )
            if _API_VALUE.fullmatch(value):
                api_paths.add(value)
            elif _WS_VALUE.fullmatch(value):
                websocket_paths.add(value)
            elif _ROUTE_VALUE.fullmatch(value):
                routes.add(value)

    return FrontendMap(
        routes=tuple(sorted(routes)),
        api_paths=tuple(sorted(api_paths)),
        websocket_paths=tuple(sorted(websocket_paths)),
        electron_bridge_references=tuple(sorted(electron)),
        static_catalog_references=tuple(sorted(static)),
    )
