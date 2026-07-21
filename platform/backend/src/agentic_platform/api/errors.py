from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from agentic_platform.auth.service import AuthorizationDenied, ResourceNotFound
from agentic_platform.domain.errors import DomainValidationError


def _response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ResourceNotFound)
    async def resource_not_found(
        request: Request,
        exc: ResourceNotFound,
    ) -> JSONResponse:
        del request
        return _response(404, "resource_not_found", str(exc))

    @app.exception_handler(AuthorizationDenied)
    async def permission_denied(
        request: Request,
        exc: AuthorizationDenied,
    ) -> JSONResponse:
        del request
        return _response(403, "permission_denied", str(exc))

    @app.exception_handler(DomainValidationError)
    async def domain_validation_error(
        request: Request,
        exc: DomainValidationError,
    ) -> JSONResponse:
        del request
        return _response(422, "domain_validation_error", str(exc))
