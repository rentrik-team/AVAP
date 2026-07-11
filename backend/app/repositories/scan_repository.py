import uuid
from typing import Optional, List, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.scan_job import ScanJob
from app.core.enums import ScanStatus


class ScanRepository:
    """Repository for managing scan job persistence."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, scan_job: ScanJob) -> ScanJob:
        """Create a new scan job."""
        self.session.add(scan_job)
        self.session.commit()
        self.session.refresh(scan_job)
        return scan_job

    def get_by_id(self, scan_id: uuid.UUID) -> Optional[ScanJob]:
        """Retrieve a scan job by its ID."""
        stmt = select(ScanJob).where(ScanJob.id == scan_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ScanJob]:
        """Retrieve all scan jobs with pagination."""
        stmt = select(ScanJob).offset(skip).limit(limit).order_by(ScanJob.created_at.desc())
        return self.session.execute(stmt).scalars().all()

    def count(self) -> int:
        """Count total scan jobs."""
        stmt = select(ScanJob)
        # Using a simpler count approach compatible with SQLAlchemy 2.0
        return len(self.session.execute(stmt).scalars().all())

    def update(self, scan_job: ScanJob) -> ScanJob:
        """Update an existing scan job."""
        self.session.commit()
        self.session.refresh(scan_job)
        return scan_job

    def delete(self, scan_job: ScanJob) -> None:
        """Delete a scan job."""
        self.session.delete(scan_job)
        self.session.commit()

    def get_running_scans_for_target(self, target_id: int) -> Sequence[ScanJob]:
        """Retrieve all running scans for a specific target."""
        stmt = select(ScanJob).where(
            ScanJob.target_id == target_id,
            ScanJob.status == ScanStatus.RUNNING
        )
        return self.session.execute(stmt).scalars().all()
