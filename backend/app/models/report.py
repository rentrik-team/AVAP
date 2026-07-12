import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import RiskLevel
from app.database.base import Base, TimestampMixin


class Report(Base, TimestampMixin):
    """Database model for a generated, immutable report artifact.

    Every successful generation request creates a new row and a new PDF
    file; reports are never overwritten or updated in place. This preserves
    a complete, auditable history of every report ever produced for a scan,
    consistent with the documented "Immutable Reports" design principle.
    Only the file name is persisted (never an absolute path); the storage
    root is always resolved from centralized configuration.
    """

    __tablename__ = "reports"

    scan_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scan_jobs.id", ondelete="CASCADE"), nullable=False, index=True
    )

    format: Mapped[str] = mapped_column(String(10), nullable=False, default="PDF")

    report_template_version: Mapped[str] = mapped_column(String(20), nullable=False)

    risk_calculation_version: Mapped[str] = mapped_column(String(20), nullable=False)

    # Snapshot of the source SCAN-scope RiskAssessment's calculated_at at the
    # moment this report was generated; establishes point-in-time freshness.
    source_risk_calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    overall_risk_score: Mapped[float] = mapped_column(Float, nullable=False)

    overall_risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risklevel"), nullable=False
    )

    vulnerability_count: Mapped[int] = mapped_column(Integer, nullable=False)

    ai_recommendations_included: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Server-generated file name only (e.g. "report_<uuid>.pdf"); the full
    # path is always resolved from settings.report_output_path at read time.
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)

    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    scan_job = relationship("ScanJob")

    __table_args__ = (
        # Defensive concurrency safeguard: two reports for the same scan can
        # never share the exact same generation timestamp.
        UniqueConstraint(
            "scan_id", "generated_at", name="uq_reports_scan_generated_at"
        ),
    )
