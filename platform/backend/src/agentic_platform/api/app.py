from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from fastapi import FastAPI

from agentic_platform.api.errors import install_error_handlers
from agentic_platform.api.health import router as health_router
from agentic_platform.api.inbox import router as inbox_router
from agentic_platform.auth.service import AuthorizationService
from agentic_platform.ports.hermes import HermesCatalog
from agentic_platform.ports.repositories import UnitOfWork


@dataclass(frozen=True, slots=True)
class ApplicationDependencies:
    unit_of_work_factory: Callable[[], UnitOfWork]
    hermes_catalog: HermesCatalog
    authorization: AuthorizationService = field(default_factory=AuthorizationService)


def create_app(dependencies: ApplicationDependencies) -> FastAPI:
    app = FastAPI(title="Agentic Platform API", version="0.1.0")
    app.state.dependencies = dependencies
    install_error_handlers(app)
    app.include_router(health_router)
    app.include_router(inbox_router)
    return app
