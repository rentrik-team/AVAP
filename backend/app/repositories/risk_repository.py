import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import RiskLevel, RiskScope
from app.models.risk_assessment import RiskAssessment


class RiskRepository:
    """Repository for managing RiskAssessment database operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, risk_id: uuid.UUID) -> RiskAssessment | None:
        """Retrieve a risk assessment by its ID."""
        stmt = select(RiskAssessment).where(RiskAssessment.id == risk_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def find_scope_record(
        self,
        scope: RiskScope,
        scan_id: uuid.UUID | None = None,
        asset_id: uuid.UUID | None = None,
        vulnerability_id: uuid.UUID | None = None,
        service_id: uuid.UUID | None = None,
    ) -> RiskAssessment | None:
        """Locate the single authoritative row for a scope/entity combination."""
        stmt = select(RiskAssessment).where(
            RiskAssessment.scope == scope,
            RiskAssessment.scan_id == scan_id,
            RiskAssessment.asset_id == asset_id,
            RiskAssessment.vulnerability_id == vulnerability_id,
            RiskAssessment.service_id == service_id,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def upsert(
        self,
        scope: RiskScope,
        risk_score: float,
        risk_level: RiskLevel,
        calculation_version: str,
        calculated_at: datetime,
        supporting_factors: dict[str, Any],
        scan_id: uuid.UUID | None = None,
        asset_id: uuid.UUID | None = None,
        vulnerability_id: uuid.UUID | None = None,
        service_id: uuid.UUID | None = None,
    ) -> RiskAssessment:
        """Create or update the authoritative risk record for a scope/entity.

        Recalculation updates the existing row in place rather than inserting
        a new one, keeping exactly one authoritative record per scope/entity.
        """
        existing = self.find_scope_record(
            scope=scope,
            scan_id=scan_id,
            asset_id=asset_id,
            vulnerability_id=vulnerability_id,
            service_id=service_id,
        )

        if existing:
            existing.risk_score = risk_score
            existing.risk_level = risk_level
            existing.calculation_version = calculation_version
            existing.calculated_at = calculated_at
            existing.supporting_factors = supporting_factors
            self.session.flush()
            return existing

        record = RiskAssessment(
            scope=scope,
            risk_score=risk_score,
            risk_level=risk_level,
            calculation_version=calculation_version,
            calculated_at=calculated_at,
            supporting_factors=supporting_factors,
            scan_id=scan_id,
            asset_id=asset_id,
            vulnerability_id=vulnerability_id,
            service_id=service_id,
        )
        self.session.add(record)
        self.session.flush()
        return record

    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        scope: RiskScope | None = None,
        risk_level: RiskLevel | None = None,
        scan_id: uuid.UUID | None = None,
    ) -> tuple[Sequence[RiskAssessment], int]:
        """Retrieve a paginated, filtered list of risk assessments."""
        stmt = select(RiskAssessment)
        count_stmt = select(func.count(RiskAssessment.id))

        filters = []
        if scope is not None:
            filters.append(RiskAssessment.scope == scope)
        if risk_level is not None:
            filters.append(RiskAssessment.risk_level == risk_level)
        if scan_id is not None:
            filters.append(RiskAssessment.scan_id == scan_id)

        if filters:
            stmt = stmt.where(*filters)
            count_stmt = count_stmt.where(*filters)

        total = self.session.execute(count_stmt).scalar() or 0

        stmt = (
            stmt.offset(skip).limit(limit).order_by(RiskAssessment.calculated_at.desc())
        )
        items = self.session.execute(stmt).scalars().all()

        return items, total

    def get_by_asset(
        self, asset_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> tuple[Sequence[RiskAssessment], int]:
        """Retrieve the paginated ASSET-scope risk history for one asset."""
        stmt = select(RiskAssessment).where(
            RiskAssessment.scope == RiskScope.ASSET,
            RiskAssessment.asset_id == asset_id,
        )
        count_stmt = select(func.count(RiskAssessment.id)).where(
            RiskAssessment.scope == RiskScope.ASSET,
            RiskAssessment.asset_id == asset_id,
        )

        total = self.session.execute(count_stmt).scalar() or 0
        stmt = (
            stmt.offset(skip).limit(limit).order_by(RiskAssessment.calculated_at.desc())
        )
        items = self.session.execute(stmt).scalars().all()

        return items, total

    def get_by_scan(self, scan_id: uuid.UUID) -> RiskAssessment | None:
        """Retrieve the singleton SCAN-scope risk assessment for one scan."""
        stmt = select(RiskAssessment).where(
            RiskAssessment.scope == RiskScope.SCAN,
            RiskAssessment.scan_id == scan_id,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_assessment(self) -> RiskAssessment | None:
        """Retrieve the singleton ASSESSMENT-scope overall risk record."""
        stmt = select(RiskAssessment).where(
            RiskAssessment.scope == RiskScope.ASSESSMENT
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_all_scan_scores(self) -> Sequence[tuple[uuid.UUID, float]]:
        """Retrieve (scan_id, risk_score) pairs for every calculated scan."""
        stmt = select(RiskAssessment.scan_id, RiskAssessment.risk_score).where(
            RiskAssessment.scope == RiskScope.SCAN
        )
        return [tuple(row) for row in self.session.execute(stmt).all()]

    def get_by_scan_and_scope(
        self, scan_id: uuid.UUID, scope: RiskScope
    ) -> Sequence[RiskAssessment]:
        """Retrieve every risk assessment of a given scope within one scan.

        Used by the Reporting Engine (Module 08) to assemble per-finding
        (VULNERABILITY-scope) and per-asset (ASSET-scope) risk detail for a
        single scan without introducing a new repository for this table.
        """
        stmt = select(RiskAssessment).where(
            RiskAssessment.scan_id == scan_id,
            RiskAssessment.scope == scope,
        )
        return self.session.execute(stmt).scalars().all()
