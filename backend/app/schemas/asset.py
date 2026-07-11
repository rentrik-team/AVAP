import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ServiceResponse(BaseModel):
    """Response model for service details."""
    id: uuid.UUID
    port: int = Field(..., ge=1, le=65535)
    protocol: str
    service_name: str
    product: Optional[str] = None
    version: Optional[str] = None
    extra_info: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetResponse(BaseModel):
    """Response model for an Asset."""
    id: uuid.UUID
    ipv4: str
    hostname: Optional[str] = None
    operating_system: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetDetailResponse(AssetResponse):
    """Detailed response model for an Asset including its open services."""
    services: List[ServiceResponse] = Field(default_factory=list)


class AssetListResponse(BaseModel):
    """Response model for a paginated list of assets."""
    assets: List[AssetResponse]
    total: int
