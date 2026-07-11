import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String, Text
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
    
    target_id: Mapped[int] = mapped_column(
        ForeignKey("targets.id", ondelete="CASCADE"), nullable=False
    )
    
    status: Mapped[ScanStatus] = mapped_column(
        Enum(ScanStatus), nullable=False, default=ScanStatus.PENDING
    )
    
    # Store the actual string for quick reference/logging
    scan_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="full"
    )
    
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Duration in seconds
    execution_duration: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    target: Mapped[Target] = relationship(lazy="joined")
