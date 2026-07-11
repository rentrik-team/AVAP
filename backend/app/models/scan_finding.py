from sqlalchemy import ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.database.base import Base, TimestampMixin


class ScanFinding(Base, TimestampMixin):
    """Database model representing an immutable observation from a specific scan job."""
    __tablename__ = "scan_findings"

    scan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scan_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    vulnerability_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vulnerabilities.id", ondelete="CASCADE"), nullable=True, index=True
    )
    
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Relationships
    scan_job = relationship("ScanJob")
    asset = relationship("Asset")
    vulnerability = relationship("Vulnerability")
    service = relationship("NetworkService")

    __table_args__ = (
        UniqueConstraint(
            "scan_id", "asset_id", "vulnerability_id", "service_id",
            name="uq_scan_findings_composite"
        ),
        Index(
            "uq_scan_findings_null_vuln",
            "scan_id", "asset_id", "service_id",
            unique=True,
            where=vulnerability_id.is_(None) & service_id.isnot(None)
        ),
        Index(
            "uq_scan_findings_null_service",
            "scan_id", "asset_id", "vulnerability_id",
            unique=True,
            where=vulnerability_id.isnot(None) & service_id.is_(None)
        ),
        Index(
            "uq_scan_findings_both_null",
            "scan_id", "asset_id",
            unique=True,
            where=vulnerability_id.is_(None) & service_id.is_(None)
        ),
    )
