"""Actor and request context abstractions for audit logging.

These are pure, framework-independent value objects. They exist so that
AVAP can express "who/what triggered this action" and "which request does
this belong to" without inventing a User model, authentication, or RBAC,
and without passing FastAPI's `Request` object into business services.

Future authentication can replace `ActorContext.anonymous()` resolution
with a real authenticated-actor resolution without changing AuditService,
AuditRepository, or the AuditEvent schema.
"""

from dataclasses import dataclass

from app.core.enums import AuditActorType

# Bounds mirror the AuditEvent column widths (see app/models/audit_event.py)
# and defend against oversized/malformed inbound values before they ever
# reach a service or the database.
MAX_ACTOR_ID_LENGTH = 100
MAX_REQUEST_ID_LENGTH = 100
MAX_SOURCE_IP_LENGTH = 45  # longest valid textual IPv6 representation


@dataclass(frozen=True)
class ActorContext:
    """Who (or what) triggered an audited action.

    Only SYSTEM and ANONYMOUS are constructible today, matching the current
    lack of authentication. `actor_id` is always None for ANONYMOUS — a
    client can never supply an actor identity that is trusted as if it were
    an authenticated user.
    """

    actor_type: AuditActorType
    actor_id: str | None = None

    @classmethod
    def anonymous(cls) -> "ActorContext":
        """The default actor for any current, unauthenticated HTTP request."""
        return cls(actor_type=AuditActorType.ANONYMOUS, actor_id=None)

    @classmethod
    def system(cls) -> "ActorContext":
        """The actor for internal orchestration with no HTTP caller."""
        return cls(actor_type=AuditActorType.SYSTEM, actor_id=None)


@dataclass(frozen=True)
class RequestContext:
    """Request-scoped correlation context, safe to persist as audit evidence.

    `source_ip` is always the direct ASGI connection address
    (`Request.client.host`), never a client-supplied forwarded header —
    AVAP has no documented trusted reverse-proxy configuration, so
    `X-Forwarded-For`/`X-Real-IP` must never be treated as authoritative.
    """

    request_id: str | None = None
    source_ip: str | None = None


@dataclass(frozen=True)
class AuditContext:
    """The complete actor + request context for one audited action."""

    actor: ActorContext
    request: RequestContext

    @classmethod
    def system(cls) -> "AuditContext":
        """Default context for service calls made outside an HTTP request
        (e.g. direct invocation in internal orchestration or tests)."""
        return cls(actor=ActorContext.system(), request=RequestContext())
