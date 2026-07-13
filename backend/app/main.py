from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware.exception_handler import setup_exception_handlers
from app.api.middleware.request_context import setup_request_context_middleware
from app.api.routes.v1.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.database.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events for the FastAPI application."""
    setup_logging()

    yield

    # Cleanup on shutdown
    engine.dispose()


def create_app() -> FastAPI:
    """Application factory for FastAPI."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Automated Vulnerability Assessment Platform API",
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS configuration. No authentication/cookies exist yet (see
    # ai_contract.md — deferred to a future phase), so credentialed
    # cross-origin requests are not a concern; allow_credentials=True
    # combined with a wildcard origin is a contradictory, browser-rejected
    # configuration and must not be reintroduced without a concrete origin
    # allowlist. Restrict allow_origins before the frontend phase begins.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register custom exception handlers
    setup_exception_handlers(app)

    # Assign/propagate a per-request correlation ID (used by audit logging)
    setup_request_context_middleware(app)

    # Include API routing
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        """Simple health check endpoint."""
        return {"status": "healthy", "version": settings.app_version}

    return app


app = create_app()
