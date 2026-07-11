import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ScanStatus


class CreateScanRequest(BaseModel):
    """Request model for creating a scan job."""
    target_id: uuid.UUID = Field(
        ...,
        description="The ID of the validated target to scan.",
    )
    scan_profile: str = Field(
        default="full",
        description="The type or profile of the scan (e.g., 'full', 'quick').",
        max_length=50,
    )
    priority: str = Field(
        default="normal",
        description="Priority of the scan job.",
        max_length=20,
    )


class ScanResponse(BaseModel):
    """Response model for a Scan Job."""
    scan_id: uuid.UUID = Field(
        description="Unique identifier for the scan job.",
        validation_alias="id"
    )
    target_id: uuid.UUID = Field(description="The ID of the associated target.")
    status: ScanStatus = Field(description="Current execution status of the scan.")
    scan_type: str = Field(description="The type of the scan.")
    created_at: datetime = Field(description="Timestamp when the scan job was requested.")
    updated_at: datetime = Field(description="Timestamp when the scan job was last updated.")
    
    started_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the scan started."
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Timestamp when the scan completed."
    )
    execution_duration: Optional[float] = Field(
        default=None, description="Execution duration in seconds."
    )
    failure_reason: Optional[str] = Field(
        default=None, description="Reason for failure if the scan failed."
    )

    model_config = ConfigDict(from_attributes=True)


class ScanListResponse(BaseModel):
    """Response model for a list of scans."""
    scans: list[ScanResponse]
    total: int


class ScanStatusResponse(BaseModel):
    """Response model for scan status."""
    scan_id: uuid.UUID
    status: ScanStatus
    updated_at: datetime
