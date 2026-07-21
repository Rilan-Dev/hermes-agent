from __future__ import annotations

import inspect
from typing import get_type_hints

from agentic_platform.ports.repositories import (
    ChannelEventRepository,
    ConversationRepository,
    MessageRepository,
    UnitOfWork,
    WorkspaceRepository,
)


def test_every_repository_operation_is_explicitly_workspace_scoped() -> None:
    protocols = (
        WorkspaceRepository,
        ConversationRepository,
        MessageRepository,
        ChannelEventRepository,
    )
    violations: list[str] = []

    for protocol in protocols:
        for name, member in inspect.getmembers(protocol, inspect.isfunction):
            if name.startswith("_"):
                continue
            parameters = list(inspect.signature(member).parameters)
            if "workspace_id" not in parameters:
                violations.append(f"{protocol.__name__}.{name}")

    assert violations == []


def test_unit_of_work_is_async_transaction_contract() -> None:
    assert inspect.iscoroutinefunction(UnitOfWork.commit)
    assert inspect.iscoroutinefunction(UnitOfWork.rollback)
    assert inspect.iscoroutinefunction(UnitOfWork.__aenter__)
    assert inspect.iscoroutinefunction(UnitOfWork.__aexit__)

    hints = get_type_hints(UnitOfWork)
    assert hints == {}
