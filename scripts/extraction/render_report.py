from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping


def _text(value: object) -> str:
    return str(value if value is not None else "").replace("|", "\\|")


def _rows(value: object) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _section_table(
    headers: tuple[str, ...], rows: Iterable[tuple[object, ...]]
) -> list[str]:
    output = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    output.extend(
        "| " + " | ".join(_text(value) for value in row) + " |" for row in rows
    )
    return output


def render_inventory_markdown(data: Mapping[str, object]) -> str:
    files = _rows(data.get("files"))
    plugins = data.get("plugins") if isinstance(data.get("plugins"), Mapping) else {}
    registries = (
        data.get("registries") if isinstance(data.get("registries"), Mapping) else {}
    )
    out_of_scope = _rows(data.get("out_of_scope_imports"))
    unresolved = _rows(data.get("unresolved_imports"))

    classifications = Counter(_text(row.get("classification")) for row in files)
    lines = [
        "# Phase 1 Extraction Inventory",
        "",
        f"- Source repository: `{_text(data.get('source_repository'))}`",
        f"- Source SHA: `{_text(data.get('source_sha'))}`",
        f"- Inventory HEAD: `{_text(data.get('inventory_head'))}`",
        f"- Scoped files: **{len(files)}**",
        f"- Out-of-scope internal dependencies: **{len(out_of_scope)}**",
        f"- Unresolved internal imports: **{len(unresolved)}**",
        "",
        "## Classification Counts",
        "",
    ]
    lines.extend(
        _section_table(
            ("Classification", "Files"),
            ((name, count) for name, count in sorted(classifications.items())),
        )
    )

    platform_plugins = _rows(plugins.get("platforms") if isinstance(plugins, Mapping) else None)
    provider_plugins = _rows(
        plugins.get("model_providers") if isinstance(plugins, Mapping) else None
    )
    lines.extend(
        [
            "",
            "## Plugin Counts",
            "",
            *_section_table(
                ("Plugin type", "Count"),
                (
                    ("platform", len(platform_plugins)),
                    ("model-provider", len(provider_plugins)),
                ),
            ),
            "",
            "## Registry Counts",
            "",
            *_section_table(
                ("Registry", "Count"),
                (
                    ("platform entries", len(registries.get("platform_entries", []))),
                    ("concrete platforms", len(registries.get("platform_concrete", []))),
                    ("deferred platforms", len(registries.get("platform_deferred", []))),
                    ("provider profiles", len(registries.get("provider_profiles", []))),
                    ("canonical providers", len(registries.get("canonical_providers", []))),
                    ("auth providers", len(registries.get("auth_providers", []))),
                    ("provider catalog", len(registries.get("provider_catalog", []))),
                ),
            ),
            "",
            "## Out-of-Scope Internal Dependencies",
            "",
        ]
    )
    if out_of_scope:
        lines.extend(
            _section_table(
                ("Source", "Dependency"),
                ((row.get("source"), row.get("dependency")) for row in out_of_scope),
            )
        )
    else:
        lines.append("None detected.")

    lines.extend(["", "## Unresolved Internal Imports", ""])
    if unresolved:
        lines.extend(
            _section_table(
                ("Source", "Import"),
                ((row.get("source"), row.get("import")) for row in unresolved),
            )
        )
    else:
        lines.append("None detected.")

    return "\n".join(lines).rstrip() + "\n"


def render_test_matrix(test_rules: object) -> str:
    rules = _rows(test_rules)
    lines = ["# Phase 1 Test Matrix", ""]
    lines.extend(
        _section_table(
            ("Kind", "Path or pattern", "Protected behavior"),
            (
                (row.get("kind"), row.get("path"), row.get("behavior"))
                for row in rules
            ),
        )
    )
    return "\n".join(lines).rstrip() + "\n"
