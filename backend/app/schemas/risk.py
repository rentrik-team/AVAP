import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import RiskLevel, RiskScope


class RiskAssessmentResponse(BaseModel):
    """Response model for a persisted, explainable risk assessment."""

    id: uuid.UUID
    scope: RiskScope
    risk_score: float = Field(..., ge=0.0, le=10.0)
    risk_level: RiskLevel
    calculation_version: str
    calculated_at: datetime
    supporting_factors: dict[str, Any]
    scan_id: uuid.UUID | None = None
    asset_id: uuid.UUID | None = None
    vulnerability_id: uuid.UUID | None = None
    service_id: uuid.UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class RiskAssessmentListResponse(BaseModel):
    """Response model for a paginated list of risk assessments."""

    risk_assessments: list[RiskAssessmentResponse]
    total: int
