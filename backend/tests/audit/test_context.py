from app.audit.context import ActorContext, AuditContext, RequestContext
from app.core.enums import AuditActorType


def test_actor_context_anonymous_has_no_actor_id():
    actor = ActorContext.anonymous()
    assert actor.actor_type == AuditActorType.ANONYMOUS
    assert actor.actor_id is None


def test_actor_context_system_has_no_actor_id():
    actor = ActorContext.system()
    assert actor.actor_type == AuditActorType.SYSTEM
    assert actor.actor_id is None


def test_actor_context_is_immutable():
    actor = ActorContext.anonymous()
    try:
        actor.actor_id = "spoofed-user"  # type: ignore[misc]
        raised = False
    except Exception:
        raised = True
    assert raised, "ActorContext must be frozen/immutable"


def test_audit_context_system_factory():
    context = AuditContext.system()
    assert context.actor.actor_type == AuditActorType.SYSTEM
    assert context.request.request_id is None
    assert context.request.source_ip is None


def test_request_context_defaults_to_none():
    request = RequestContext()
    assert request.request_id is None
    assert request.source_ip is None


def test_client_supplied_actor_id_cannot_reach_anonymous_context():
    """There is no constructor path from arbitrary client input to a
    trusted actor_id on an ANONYMOUS actor — anonymous() takes no
    parameters at all.
    """
    actor = ActorContext.anonymous()
    assert actor.actor_id is None
