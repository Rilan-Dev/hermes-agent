from __future__ import annotations

from pathlib import Path


WORKFLOW = Path(".github/workflows/tests.yml")


def test_python_workflow_runs_permanent_postgres_contract_gate() -> None:
    content = WORKFLOW.read_text(encoding="utf-8")

    required_fragments = (
        "platform-postgres:",
        'name: "Platform PostgreSQL contracts"',
        "image: postgres:16-alpine",
        "POSTGRES_TEST_DSN:",
        "--extra all --extra dev --extra matrix",
        "test_live_repository_contract.py",
        "test_live_ingestion.py",
        "python -m pytest platform/backend/tests -q",
    )
    for fragment in required_fragments:
        assert fragment in content
