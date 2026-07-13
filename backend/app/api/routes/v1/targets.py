import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.audit import get_audit_context, get_audit_service
from app.api.dependencies.database import get_db
from app.api.responses.api_response import SuccessResponse
from app.audit.context import AuditContext
from app.repositories.target_repository import TargetRepository
from app.schemas.target import (
    CreateTargetRequest,
    TargetListResponse,
    TargetResponse,
    UpdateTargetRequest,
)
from app.services.audit_service import AuditService
from app.services.target_service import TargetService

router = APIRouter()


def get_target_service(
    db: Session = Depends(get_db),
    audit_service: AuditService = Depends(get_audit_service),
) -> TargetService:
    """Dependency to inject TargetService into routes."""
    repository = TargetRepository(db)
    return TargetService(repository, audit_service=audit_service)


@router.post(
    "",
    response_model=SuccessResponse[TargetResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new target",
)
def create_target(
    request: CreateTargetRequest,
    service: TargetService = Depends(get_target_service),
    audit_context: AuditContext = Depends(get_audit_context),
) -> dict:
    """Register a new scan target (IPv4, CIDR, or Hostname).

    The target is validated, normalized, and checked for duplicates
    before being persisted.
    """
    target = service.create_target(request, audit_context=audit_context)
    # Convert SQLAlchemy model to Pydantic model for response
    target_resp = TargetResponse.model_validate(target)
    return {"data": target_resp}


@router.get(
    "",
    response_model=SuccessResponse[TargetListResponse],
    summary="Get all targets",
)
def get_targets(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    service: TargetService = Depends(get_target_service),
) -> dict:
    """Retrieve a paginated list of all targets."""
    targets, total = service.get_all_targets(skip=skip, limit=limit)
    target_responses = [TargetResponse.model_validate(t) for t in targets]
    return {"data": TargetListResponse(targets=target_responses, total=total)}


@router.get(
    "/{target_id}",
    response_model=SuccessResponse[TargetResponse],
    summary="Get a single target",
)
def get_target(
    target_id: uuid.UUID,
    service: TargetService = Depends(get_target_service),
) -> dict:
    """Retrieve a specific target by its UUID."""
    target = service.get_target(target_id)
    return {"data": TargetResponse.model_validate(target)}


@router.put(
    "/{target_id}",
    response_model=SuccessResponse[TargetResponse],
    summary="Update a target",
)
def update_target(
    target_id: uuid.UUID,
    request: UpdateTargetRequest,
    service: TargetService = Depends(get_target_service),
    audit_context: AuditContext = Depends(get_audit_context),
) -> dict:
    """Update an existing target.

    The new target value is validated and normalized.
    """
    target = service.update_target(target_id, request, audit_context=audit_context)
    return {"data": TargetResponse.model_validate(target)}


@router.delete(
    "/{target_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a target",
)
def delete_target(
    target_id: uuid.UUID,
    service: TargetService = Depends(get_target_service),
    audit_context: AuditContext = Depends(get_audit_context),
) -> None:
    """Delete a target from the system."""
    service.delete_target(target_id, audit_context=audit_context)
