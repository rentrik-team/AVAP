import uuid
from datetime import datetime

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
        description="Unique identifier for the scan job.", validation_alias="id"
    )
    target_id: uuid.UUID = Field(description="The ID of the associated target.")
    status: ScanStatus = Field(description="Current execution status of the scan.")
    scan_type: str = Field(description="The type of the scan.")
    created_at: datetime = Field(
        description="Timestamp when the scan job was requested."
    )
    updated_at: datetime = Field(
        description="Timestamp when the scan job was last updated."
    )

    started_at: datetime | None = Field(
        default=None, description="Timestamp when the scan started."
    )
    completed_at: datetime | None = Field(
        default=None, description="Timestamp when the scan completed."
    )
    execution_duration: float | None = Field(
        default=None, description="Execution duration in seconds."
    )
    failure_reason: str | None = Field(
        default=None, description="Reason for failure if the scan failed."
    )
    output_file_path: str | None = Field(
        default=None,
        description="Path to the scanner's raw output file (populated even for "
        "cancelled/timed-out runs, since scanners flush results incrementally).",
    )
    stdout_log: str | None = Field(
        default=None, description="Captured stdout from the scanner process."
    )
    stderr_log: str | None = Field(
        default=None, description="Captured stderr from the scanner process."
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
