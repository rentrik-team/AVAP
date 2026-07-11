import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.api.responses.api_response import SuccessResponse
from app.core.exceptions import NotFoundException
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.schemas.vulnerability import VulnerabilityListResponse, VulnerabilityResponse

router = APIRouter()


def get_vulnerability_repository(db: Session = Depends(get_db)) -> VulnerabilityRepository:
    """Dependency to inject VulnerabilityRepository into routes."""
    return VulnerabilityRepository(db)


@router.get(
    "",
    response_model=SuccessResponse[VulnerabilityListResponse],
    summary="Get all vulnerabilities",
)
def list_vulnerabilities(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    severity_rating: str | None = Query(None, description="Filter by severity rating (Low, Medium, High, Critical, None)"),
    cve: str | None = Query(None, description="Filter by CVE ID"),
    repository: VulnerabilityRepository = Depends(get_vulnerability_repository),
) -> dict:
    """Retrieve a paginated, filtered list of all normalized vulnerabilities."""
    items, total = repository.get_all(
        skip=skip,
        limit=limit,
        severity_rating=severity_rating,
        cve=cve
    )
    
    vulnerability_responses = [VulnerabilityResponse.model_validate(item) for item in items]
    return {
        "data": VulnerabilityListResponse(vulnerabilities=vulnerability_responses, total=total)
    }


@router.get(
    "/{vuln_id}",
    response_model=SuccessResponse[VulnerabilityResponse],
    summary="Get vulnerability details",
)
def get_vulnerability(
    vuln_id: uuid.UUID,
    repository: VulnerabilityRepository = Depends(get_vulnerability_repository),
) -> dict:
    """Retrieve details of a specific vulnerability by its UUID."""
    vulnerability = repository.get_by_id(vuln_id)
    if not vulnerability:
        raise NotFoundException(f"Vulnerability with ID {vuln_id} not found.")
    
    return {"data": VulnerabilityResponse.model_validate(vulnerability)}
