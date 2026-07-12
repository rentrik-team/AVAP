import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, Enum, Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.enums import RiskLevel, RiskScope
from app.database.base import Base, TimestampMixin

# Portable JSON type: renders as JSONB on PostgreSQL, plain JSON on SQLite (tests).
SupportingFactorsType = JSONB().with_variant(JSON(), "sqlite")


class RiskAssessment(Base, TimestampMixin):
    """Database model for deterministic risk assessments at an explicit scope.

    A single row always represents exactly one of four scopes (VULNERABILITY,
    ASSET, SCAN, ASSESSMENT). The scope determines which entity foreign keys
    are required versus forbidden; this invariant is enforced by a database
    CHECK constraint rather than inferred from nullable-column combinations.
    """

    __tablename__ = "risk_assessments"

    scope: Mapped[RiskScope] = mapped_column(
        Enum(RiskScope, name="riskscope"), nullable=False, index=True
    )

    risk_score: Mapped[float] = mapped_column(Float, nullable=False)

    risk_level: Mapped[RiskLevel] = mapped_column(
        Enum(RiskLevel, name="risklevel"), nullable=False
    )

    calculation_version: Mapped[str] = mapped_column(String(20), nullable=False)

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Supporting factors for explainability (deterministic inputs behind the score).
    supporting_factors: Mapped[dict[str, Any]] = mapped_column(
        SupportingFactorsType, nullable=False, default=dict
    )

    # Scope-dependent entity associations.
    scan_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("scan_jobs.id", ondelete="CASCADE"), nullable=True, index=True
    )

    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"), nullable=True, index=True
    )

    vulnerability_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("vulnerabilities.id", ondelete="CASCADE"), nullable=True, index=True
    )

    service_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("services.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Relationships (read-only association; owning models are never modified).
    scan_job = relationship("ScanJob")
    asset = relationship("Asset")
    vulnerability = relationship("Vulnerability")
    service = relationship("NetworkService")

    __table_args__ = (
        CheckConstraint(
            "(scope = 'VULNERABILITY' AND scan_id IS NOT NULL AND asset_id IS NOT NULL "
            "AND vulnerability_id IS NOT NULL) OR "
            "(scope = 'ASSET' AND scan_id IS NOT NULL AND asset_id IS NOT NULL "
            "AND vulnerability_id IS NULL AND service_id IS NULL) OR "
            "(scope = 'SCAN' AND scan_id IS NOT NULL AND asset_id IS NULL "
            "AND vulnerability_id IS NULL AND service_id IS NULL) OR "
            "(scope = 'ASSESSMENT' AND scan_id IS NULL AND asset_id IS NULL "
            "AND vulnerability_id IS NULL AND service_id IS NULL)",
            name="chk_risk_assessment_scope_invariants",
        ),
        # Partial unique indexes enforce one authoritative row per scope/entity
        # combination, making recalculation an in-place update rather than an insert.
        Index(
            "uq_risk_vulnerability_with_service",
            "scan_id",
            "asset_id",
            "vulnerability_id",
            "service_id",
            unique=True,
            sqlite_where=(scope == RiskScope.VULNERABILITY) & (service_id.isnot(None)),
            postgresql_where=(scope == RiskScope.VULNERABILITY)
            & (service_id.isnot(None)),
        ),
        Index(
            "uq_risk_vulnerability_without_service",
            "scan_id",
            "asset_id",
            "vulnerability_id",
            unique=True,
            sqlite_where=(scope == RiskScope.VULNERABILITY) & (service_id.is_(None)),
            postgresql_where=(scope == RiskScope.VULNERABILITY)
            & (service_id.is_(None)),
        ),
        Index(
            "uq_risk_asset",
            "scan_id",
            "asset_id",
            unique=True,
            sqlite_where=scope == RiskScope.ASSET,
            postgresql_where=scope == RiskScope.ASSET,
        ),
        Index(
            "uq_risk_scan",
            "scan_id",
            unique=True,
            sqlite_where=scope == RiskScope.SCAN,
            postgresql_where=scope == RiskScope.SCAN,
        ),
        Index(
            "uq_risk_assessment_singleton",
            "scope",
            unique=True,
            sqlite_where=scope == RiskScope.ASSESSMENT,
            postgresql_where=scope == RiskScope.ASSESSMENT,
        ),
    )
