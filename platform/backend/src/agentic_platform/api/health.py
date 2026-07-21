from __future__ import annotations

from fastapi import APIRouter, Request


router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict[str, str]:
    dependencies = request.app.state.dependencies
    try:
        async with dependencies.unit_of_work_factory() as uow:
            await uow.rollback()
        storage = "ready"
    except Exception:
        storage = "unready"

    try:
        hermes = "ready" if await dependencies.hermes_catalog.ready() else "unready"
    except Exception:
        hermes = "unready"

    status = "ok" if storage == "ready" and hermes == "ready" else "degraded"
    return {
        "status": status,
        "process": "healthy",
        "storage": storage,
        "hermes": hermes,
    }
