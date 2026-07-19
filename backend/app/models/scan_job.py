import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ScanStatus
from app.database.base import Base, TimestampMixin
from app.models.target import Target


class ScanJob(Base, TimestampMixin):
    """Database model for scan jobs.

    A scan job orchestrates the vulnerability assessment process for a specific target.
    """

    __tablename__ = "scan_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    target_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("targets.id", ondelete="CASCADE"), nullable=False, index=True
    )

    status: Mapped[ScanStatus] = mapped_column(
        Enum(ScanStatus), nullable=False, default=ScanStatus.PENDING
    )

    # Store the actual string for quick reference/logging
    scan_type: Mapped[str] = mapped_column(String(50), nullable=False, default="full")

    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Duration in seconds
    execution_duration: Mapped[float | None] = mapped_column(nullable=True)

    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Path to the scanner's raw output file (e.g. Nmap XML), populated even
    # for cancelled/timed-out runs since scanners flush output incrementally.
    output_file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    stdout_log: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr_log: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    target: Mapped[Target] = relationship(lazy="joined")

    __table_args__ = (Index("ix_scan_jobs_created_at", "created_at"),)
