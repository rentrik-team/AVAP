"""Minimal per-request correlation ID middleware.

AVAP has no existing request/correlation ID mechanism. This is the minimum
safe implementation: reuse a well-formed inbound `X-Request-ID` header, or
generate a fresh server-side UUID4 otherwise. No distributed tracing, no
OpenTelemetry, no second competing ID scheme.
"""

import re
import uuid

from fastapi import FastAPI, Request

# Bounded length, restricted to a safe charset. Anything else (control
# characters, unbounded length, unexpected symbols) is treated as absent.
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9\-]{1,100}$")


def _resolve_request_id(inbound: str | None) -> str:
    if inbound and _REQUEST_ID_PATTERN.fullmatch(inbound):
        return inbound
    return str(uuid.uuid4())


def setup_request_context_middleware(app: FastAPI) -> None:
    """Register the request-ID middleware with the FastAPI application."""

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        request_id = _resolve_request_id(request.headers.get("x-request-id"))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
