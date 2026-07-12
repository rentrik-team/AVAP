"""Risk Calculation Engine: computes the deterministic score for one vulnerability."""

from dataclasses import dataclass
from typing import Any

from app.core.enums import RiskLevel
from app.risk_engine import rules
from app.risk_engine.context import RiskContext


@dataclass(frozen=True)
class VulnerabilityRiskResult:
    """Deterministic risk result for a single vulnerability occurrence."""

    score: float
    level: RiskLevel
    supporting_factors: dict[str, Any]


def calculate_vulnerability_risk(
    severity_score: float,
    severity_rating: str,
    context: RiskContext,
) -> VulnerabilityRiskResult:
    """Calculate the deterministic risk score for a single vulnerability occurrence.

    Args:
        severity_score: Scanner-reported CVSS score (0.0 when unavailable).
        severity_rating: Normalized severity rating (None, Low, Medium, High, Critical).
        context: Contextual exposure factors for this vulnerability.

    Returns:
        A VulnerabilityRiskResult with the bounded score, risk level, and the
        exact supporting factors used to derive it.
    """
    base_score, cvss_used = rules.base_score_for(severity_score, severity_rating)
    asset_bonus = rules.asset_influence_bonus(context.affected_asset_count)
    service_bonus = rules.service_influence_bonus(context.affected_service_count)

    final_score = rules.clamp_score(base_score + asset_bonus + service_bonus)
    level = rules.risk_level_for(final_score)

    supporting_factors = {
        "base_score": base_score,
        "cvss_used": cvss_used,
        "severity_rating": severity_rating,
        "affected_asset_count": context.affected_asset_count,
        "affected_service_count": context.affected_service_count,
        "asset_influence_bonus": asset_bonus,
        "service_influence_bonus": service_bonus,
    }

    return VulnerabilityRiskResult(
        score=final_score, level=level, supporting_factors=supporting_factors
    )
