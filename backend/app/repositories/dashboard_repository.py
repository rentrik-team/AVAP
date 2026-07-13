import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import Row, exists, func, select
from sqlalchemy.orm import Session

from app.core.enums import RiskScope, ScanStatus
from app.models.ai_recommendation import AIRecommendation
from app.models.asset import Asset
from app.models.report import Report
from app.models.risk_assessment import RiskAssessment
from app.models.scan_finding import ScanFinding
from app.models.scan_job import ScanJob
from app.models.service import NetworkService
from app.models.target import Target
from app.models.vulnerability import Vulnerability


class DashboardRepository:
    """Read-only repository for cross-domain dashboard aggregate queries.

    Every method performs a single, bounded, aggregate SQL query. This
    repository never adds, updates, deletes, flushes, or commits data, and
    never re-derives risk or severity — it only reads what upstream modules
    have already persisted.
    """

    def __init__(self, session: Session):
        self.session = session

    # --- Simple counts ---

    def count_targets(self) -> int:
        return self.session.execute(select(func.count(Target.id))).scalar() or 0

    def count_scans(self) -> int:
        return self.session.execute(select(func.count(ScanJob.id))).scalar() or 0

    def count_assets(self) -> int:
        return self.session.execute(select(func.count(Asset.id))).scalar() or 0

    def count_network_services(self) -> int:
        return self.session.execute(select(func.count(NetworkService.id))).scalar() or 0

    def count_vulnerabilities(self) -> int:
        return self.session.execute(select(func.count(Vulnerability.id))).scalar() or 0

    def count_scan_findings(self) -> int:
        return self.session.execute(select(func.count(ScanFinding.id))).scalar() or 0

    def count_ai_recommendations(self) -> int:
        return (
            self.session.execute(select(func.count(AIRecommendation.id))).scalar() or 0
        )

    # --- Scan statistics ---

    def get_scan_status_distribution(self) -> dict[ScanStatus, int]:
        stmt = select(ScanJob.status, func.count(ScanJob.id)).group_by(ScanJob.status)
        return dict(self.session.execute(stmt).all())

    def get_average_scan_duration_seconds(self) -> float | None:
        stmt = select(func.avg(ScanJob.execution_duration)).where(
            ScanJob.execution_duration.isnot(None)
        )
        return self.session.execute(stmt).scalar()

    def get_recent_scans(self, limit: int) -> Sequence[ScanJob]:
        stmt = select(ScanJob).order_by(ScanJob.created_at.desc()).limit(limit)
        return self.session.execute(stmt).scalars().all()

    # --- Asset statistics ---

    def get_recently_discovered_assets(self, limit: int) -> Sequence[Asset]:
        stmt = select(Asset).order_by(Asset.created_at.desc()).limit(limit)
        return self.session.execute(stmt).scalars().all()

    # --- Vulnerability statistics ---

    def get_vulnerability_severity_distribution(self) -> dict[str, int]:
        stmt = select(
            Vulnerability.severity_rating, func.count(Vulnerability.id)
        ).group_by(Vulnerability.severity_rating)
        return dict(self.session.execute(stmt).all())

    # --- Risk statistics ---
    #
    # "Current" per-entity risk is defined as the worst (maximum risk_score)
    # RiskAssessment ever persisted for that entity, mirroring Module 06's
    # own "maximum of children" aggregation philosophy rather than a
    # newly-invented "latest scan wins" rule. Ties are broken by the
    # RiskAssessment's own id for full determinism.

    def _ranked_asset_risk_subquery(self):
        return (
            select(
                RiskAssessment.id.label("risk_id"),
                RiskAssessment.asset_id.label("asset_id"),
                RiskAssessment.risk_score.label("risk_score"),
                RiskAssessment.risk_level.label("risk_level"),
                Asset.ipv4.label("ipv4"),
                Asset.hostname.label("hostname"),
                func.row_number()
                .over(
                    partition_by=RiskAssessment.asset_id,
                    order_by=(
                        RiskAssessment.risk_score.desc(),
                        RiskAssessment.id.asc(),
                    ),
                )
                .label("rn"),
            )
            .join(Asset, RiskAssessment.asset_id == Asset.id)
            .where(RiskAssessment.scope == RiskScope.ASSET)
            .subquery()
        )

    def get_top_risk_assets(self, limit: int) -> Sequence[Row]:
        ranked = self._ranked_asset_risk_subquery()
        stmt = (
            select(ranked)
            .where(ranked.c.rn == 1)
            .order_by(ranked.c.risk_score.desc(), ranked.c.ipv4.asc())
            .limit(limit)
        )
        return self.session.execute(stmt).all()

    def get_asset_risk_level_distribution(self) -> dict[str, int]:
        ranked = self._ranked_asset_risk_subquery()
        stmt = (
            select(ranked.c.risk_level, func.count())
            .where(ranked.c.rn == 1)
            .group_by(ranked.c.risk_level)
        )
        return dict(self.session.execute(stmt).all())

    def _ranked_vulnerability_risk_subquery(self):
        return (
            select(
                RiskAssessment.id.label("risk_id"),
                RiskAssessment.vulnerability_id.label("vulnerability_id"),
                RiskAssessment.risk_score.label("risk_score"),
                RiskAssessment.risk_level.label("risk_level"),
                Vulnerability.name.label("name"),
                Vulnerability.cve.label("cve"),
                Vulnerability.severity_rating.label("severity_rating"),
                func.row_number()
                .over(
                    partition_by=RiskAssessment.vulnerability_id,
                    order_by=(
                        RiskAssessment.risk_score.desc(),
                        RiskAssessment.id.asc(),
                    ),
                )
                .label("rn"),
            )
            .join(Vulnerability, RiskAssessment.vulnerability_id == Vulnerability.id)
            .where(RiskAssessment.scope == RiskScope.VULNERABILITY)
            .subquery()
        )

    def get_top_risk_vulnerabilities(self, limit: int) -> Sequence[Row]:
        ranked = self._ranked_vulnerability_risk_subquery()
        stmt = (
            select(ranked)
            .where(ranked.c.rn == 1)
            .order_by(ranked.c.risk_score.desc(), ranked.c.name.asc())
            .limit(limit)
        )
        return self.session.execute(stmt).all()

    def get_affected_asset_counts(
        self, vulnerability_ids: Sequence[uuid.UUID]
    ) -> dict[uuid.UUID, int]:
        """Distinct asset count per vulnerability, bounded to the given IDs.

        A single grouped query regardless of how many vulnerability IDs are
        supplied; never one query per vulnerability.
        """
        if not vulnerability_ids:
            return {}
        stmt = (
            select(
                RiskAssessment.vulnerability_id,
                func.count(func.distinct(RiskAssessment.asset_id)),
            )
            .where(
                RiskAssessment.scope == RiskScope.VULNERABILITY,
                RiskAssessment.vulnerability_id.in_(vulnerability_ids),
            )
            .group_by(RiskAssessment.vulnerability_id)
        )
        return dict(self.session.execute(stmt).all())

    # --- Report statistics ---

    def get_reports_by_format(self) -> dict[str, int]:
        stmt = select(Report.format, func.count(Report.id)).group_by(Report.format)
        return dict(self.session.execute(stmt).all())

    def get_latest_report_generated_at(self) -> datetime | None:
        return self.session.execute(select(func.max(Report.generated_at))).scalar()

    # --- AI recommendation statistics ---

    def get_recommendations_by_provider(self) -> dict[str, int]:
        stmt = select(
            AIRecommendation.provider, func.count(AIRecommendation.id)
        ).group_by(AIRecommendation.provider)
        return dict(self.session.execute(stmt).all())

    def get_recommendations_by_model(self) -> dict[str, int]:
        stmt = select(AIRecommendation.model, func.count(AIRecommendation.id)).group_by(
            AIRecommendation.model
        )
        return dict(self.session.execute(stmt).all())

    def get_recommendations_by_severity(self) -> dict[str, int]:
        stmt = (
            select(Vulnerability.severity_rating, func.count(AIRecommendation.id))
            .join(Vulnerability, AIRecommendation.vulnerability_id == Vulnerability.id)
            .group_by(Vulnerability.severity_rating)
        )
        return dict(self.session.execute(stmt).all())

    def get_remediation_coverage_counts(self) -> tuple[int, int]:
        """Return (eligible_count, current_count) for remediation coverage.

        `eligible_count` is every persisted VULNERABILITY-scope risk
        assessment. `current_count` is the subset with at least one
        AIRecommendation whose generated_at is not older than the risk
        assessment's own calculated_at (Module 07's freshness rule),
        evaluated via a correlated EXISTS subquery (single query, no loop).
        """
        eligible = (
            self.session.execute(
                select(func.count(RiskAssessment.id)).where(
                    RiskAssessment.scope == RiskScope.VULNERABILITY
                )
            ).scalar()
            or 0
        )

        current = (
            self.session.execute(
                select(func.count(RiskAssessment.id)).where(
                    RiskAssessment.scope == RiskScope.VULNERABILITY,
                    exists().where(
                        AIRecommendation.risk_assessment_id == RiskAssessment.id,
                        AIRecommendation.generated_at >= RiskAssessment.calculated_at,
                    ),
                )
            ).scalar()
            or 0
        )
        return eligible, current
