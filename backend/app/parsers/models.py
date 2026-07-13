import uuid
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.core.enums import ScannerType


class ParsedVulnerability(BaseModel):
    """Unified representation of an extracted vulnerability finding."""

    name: str = Field(..., description="Vulnerability name or title")
    severity_score: float = Field(
        0.0, ge=0.0, le=10.0, description="CVSS severity score (0.0 - 10.0)"
    )
    severity_rating: str = Field(
        "None", description="Text rating (None, Low, Medium, High, Critical)"
    )
    description: str = Field("", description="Detailed finding description")
    cve: str | None = Field(None, description="CVE identifier (e.g. CVE-2023-1234)")
    port: int | None = Field(
        None, ge=1, le=65535, description="Port number associated with finding"
    )
    protocol: str | None = Field(
        None, description="Protocol associated with finding (tcp/udp)"
    )
    references: list[str] = Field(
        default_factory=list, description="External reference URLs"
    )

    @field_validator("severity_rating")
    @classmethod
    def validate_rating(cls, val: str) -> str:
        allowed = {"None", "Low", "Medium", "High", "Critical"}
        title_val = val.strip().title()
        if title_val not in allowed:
            # Fallback to None if not matched
            return "None"
        return title_val


class ParsedService(BaseModel):
    """Unified representation of an extracted network service."""

    port: int = Field(..., ge=1, le=65535, description="Port number")
    protocol: str = Field(..., description="Transport protocol (tcp/udp)")
    service_name: str = Field(
        "unknown", description="Enumerated service name (e.g. http, ssh)"
    )
    product: str | None = Field(None, description="Software product name")
    version: str | None = Field(None, description="Software version")
    extra_info: str | None = Field(
        None, description="Extra banner information or details"
    )
    vulnerabilities: list[ParsedVulnerability] = Field(
        default_factory=list, description="Vulnerabilities detected on this service"
    )


class ParsedHost(BaseModel):
    """Unified representation of an extracted host/asset."""

    ipv4: str = Field(..., description="IPv4 address of the scanned target host")
    hostname: str | None = Field(None, description="Extracted hostname")
    operating_system: str | None = Field(None, description="Detected operating system")
    services: list[ParsedService] = Field(
        default_factory=list, description="Services found open on this host"
    )


class AssessmentPackage(BaseModel):
    """Standardized package containing all parsed and normalized scan results."""

    scan_id: uuid.UUID = Field(..., description="Associated Scan Job ID")
    scanner_type: ScannerType = Field(
        ..., description="Scanner implementation that generated data"
    )
    parsed_hosts: list[ParsedHost] = Field(
        default_factory=list, description="List of hosts found during assessment"
    )
    execution_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata from scanner run"
    )
    parsed_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Parsing timestamp"
    )
