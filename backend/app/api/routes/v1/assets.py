import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.database import get_db
from app.api.responses.api_response import SuccessResponse
from app.core.exceptions import NotFoundException
from app.repositories.asset_repository import AssetRepository
from app.schemas.asset import AssetDetailResponse, AssetListResponse, AssetResponse

router = APIRouter()


def get_asset_repository(db: Session = Depends(get_db)) -> AssetRepository:
    """Dependency to inject AssetRepository into routes."""
    return AssetRepository(db)


@router.get(
    "",
    response_model=SuccessResponse[AssetListResponse],
    summary="Get all assets",
)
def list_assets(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Max records to return"),
    ip: str | None = Query(None, description="Filter by IP address"),
    hostname: str | None = Query(None, description="Filter by hostname"),
    port: int | None = Query(None, description="Filter by open port"),
    cve: str | None = Query(None, description="Filter by vulnerability CVE"),
    repository: AssetRepository = Depends(get_asset_repository),
) -> dict:
    """Retrieve a paginated, filtered list of assets."""
    items, total = repository.get_all(
        skip=skip,
        limit=limit,
        ip=ip,
        hostname=hostname,
        port=port,
        cve=cve
    )
    
    asset_responses = [AssetResponse.model_validate(item) for item in items]
    return {
        "data": AssetListResponse(assets=asset_responses, total=total)
    }


@router.get(
    "/{asset_id}",
    response_model=SuccessResponse[AssetDetailResponse],
    summary="Get asset details",
)
def get_asset(
    asset_id: uuid.UUID,
    repository: AssetRepository = Depends(get_asset_repository),
) -> dict:
    """Retrieve details of a specific asset including open network services."""
    asset = repository.get_by_id(asset_id)
    if not asset:
        raise NotFoundException(f"Asset with ID {asset_id} not found.")
    
    return {"data": AssetDetailResponse.model_validate(asset)}


@router.delete(
    "/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an asset",
)
def delete_asset(
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    repository: AssetRepository = Depends(get_asset_repository),
) -> None:
    """Delete an asset from the system."""
    asset = repository.get_by_id(asset_id)
    if not asset:
        raise NotFoundException(f"Asset with ID {asset_id} not found.")
    
    repository.delete(asset)
    db.commit()
