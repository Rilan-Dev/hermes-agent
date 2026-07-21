from pathlib import Path

from scripts.platform_inventory.frontend_map import scan_frontend


def test_scan_frontend_maps_routes_api_websocket_and_electron_bridge(tmp_path: Path) -> None:
    web = tmp_path / "web" / "src"
    desktop = tmp_path / "apps" / "desktop" / "src"
    shared = tmp_path / "apps" / "shared"
    web.mkdir(parents=True)
    desktop.mkdir(parents=True)
    shared.mkdir(parents=True)
    (web / "App.tsx").write_text(
        'const routes = {"/channels": ChannelsPage};\n'
        'fetch("/api/messaging/platforms");\n'
        'new WebSocket("/ws/chat");\n',
        encoding="utf-8",
    )
    (desktop / "hermes.ts").write_text(
        "window.hermesDesktop?.terminal;\n"
        "const MESSAGING_SESSION_SOURCE_IDS = ['telegram'];\n",
        encoding="utf-8",
    )
    (shared / "catalog.ts").write_text(
        "export const CANONICAL_PROVIDERS = ['openai-api'];\n",
        encoding="utf-8",
    )

    result = scan_frontend(tmp_path)

    assert result.routes == ("/channels",)
    assert result.api_paths == ("/api/messaging/platforms",)
    assert result.websocket_paths == ("/ws/chat",)
    assert result.electron_bridge_references == (
        "apps/desktop/src/hermes.ts:hermesDesktop",
    )
    assert result.static_catalog_references == (
        "apps/desktop/src/hermes.ts:MESSAGING_SESSION_SOURCE_IDS",
        "apps/shared/catalog.ts:CANONICAL_PROVIDERS",
    )


def test_scan_frontend_ignores_comments_and_non_source_files(tmp_path: Path) -> None:
    web = tmp_path / "web" / "src"
    web.mkdir(parents=True)
    (web / "ignored.txt").write_text('"/api/not-source"\n', encoding="utf-8")
    (web / "comments.ts").write_text(
        '// fetch("/api/comment-only")\n'
        'const docs = "https://example.test/api/external";\n',
        encoding="utf-8",
    )

    result = scan_frontend(tmp_path)

    assert "/api/not-source" not in result.api_paths
    assert "/api/external" not in result.api_paths


def test_scan_frontend_decodes_js_escapes_without_python_escape_warnings(
    tmp_path: Path,
) -> None:
    import warnings

    web = tmp_path / "web" / "src"
    web.mkdir(parents=True)
    (web / "escaped.ts").write_text(
        'const label = "Café";\n'
        'const unknown = "\\q";\n'
        'fetch("\\/api\\/messaging\\/platforms");\n',
        encoding="utf-8",
    )

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        result = scan_frontend(tmp_path)

    assert result.api_paths == ("/api/messaging/platforms",)
