import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import TargetType


class TargetBase(BaseModel):
    """Base schema for Target data."""
    target: str = Field(
        ...,
        description="The IP address, CIDR range, or hostname to scan.",
        min_length=1,
        max_length=253,
    )


class CreateTargetRequest(TargetBase):
    """Request model for creating a target."""
    pass


class UpdateTargetRequest(TargetBase):
    """Request model for updating an existing target."""
    pass


class TargetResponse(TargetBase):
    """Response model for a Target."""
    id: uuid.UUID = Field(description="Unique identifier for the target.")
    target_type: TargetType = Field(description="The classified type of the target.")
    created_at: datetime = Field(description="Timestamp when the target was created.")
    updated_at: datetime = Field(description="Timestamp when the target was last updated.")

    model_config = ConfigDict(from_attributes=True)


class TargetListResponse(BaseModel):
    """Response model for a list of targets."""
    targets: list[TargetResponse]
    total: int
