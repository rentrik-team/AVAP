import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.scan_finding import ScanFinding


class ScanFindingRepository:
    """Read-only repository for querying persisted scan findings."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_scan(self, scan_id: uuid.UUID) -> Sequence[ScanFinding]:
        """Retrieve all findings for a scan, with vulnerability data eager loaded."""
        stmt = (
            select(ScanFinding)
            .where(ScanFinding.scan_id == scan_id)
            .options(selectinload(ScanFinding.vulnerability))
        )
        return self.session.execute(stmt).scalars().all()
