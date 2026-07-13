from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.audit.context import ActorContext, AuditContext, RequestContext
from app.repositories.audit_repository import AuditRepository
from app.services.audit_service import AuditService


def get_audit_context(request: Request) -> AuditContext:
    """Resolve the actor + request context for the current HTTP request.

    Every current HTTP request resolves to an ANONYMOUS actor: AVAP has no
    authentication, so no caller identity can be established, and no
    client-supplied header is ever trusted as an actor identity.
    `source_ip` is always the direct ASGI connection address — never a
    forwarded header, since no trusted reverse-proxy configuration exists.
    """
    request_id = getattr(request.state, "request_id", None)
    source_ip = request.client.host if request.client else None
    return AuditContext(
        actor=ActorContext.anonymous(),
        request=RequestContext(request_id=request_id, source_ip=source_ip),
    )


def get_audit_service(db: Session = Depends(get_db)) -> AuditService:
    """Dependency to inject a fully constructed AuditService into routes."""
    return AuditService(AuditRepository(db))
