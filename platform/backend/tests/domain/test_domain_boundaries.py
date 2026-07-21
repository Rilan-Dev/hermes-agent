import ast
from pathlib import Path


DISALLOWED_ROOTS = {
    "fastapi",
    "sqlalchemy",
    "asyncpg",
    "redis",
    "boto3",
    "gateway",
    "hermes_cli",
    "agent",
    "tools",
}


def test_domain_package_has_no_infrastructure_or_hermes_imports() -> None:
    domain = Path("platform/backend/src/agentic_platform/domain")
    violations: list[str] = []

    for path in sorted(domain.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            for module in modules:
                root = module.split(".", 1)[0]
                if root in DISALLOWED_ROOTS:
                    violations.append(f"{path}:{module}")

    assert violations == []
