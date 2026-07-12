"""Deterministic scoring rules for the Risk Engine.

Every constant governing risk calculation is centralized here. No scoring
constant, severity mapping, or threshold may be defined anywhere else.
"""

from app.core.enums import RiskLevel

# Version identifier persisted on every calculated risk record. Bump this
# whenever a rule in this module changes the numeric outcome of a calculation.
CALCULATION_VERSION = "1.0.0"

# Bounded score range enforced on every calculated risk score.
SCORE_MIN = 0.0
SCORE_MAX = 10.0

# Fallback base score per severity rating, used only when a vulnerability has
# no CVSS score (severity_score == 0.0). Mirrors the CVSS band midpoints used
# by app.parsers.openvas_parser.OpenVASParser._map_cvss_to_severity_rating so
# that severity language stays consistent across the platform.
SEVERITY_BASE_SCORES: dict[str, float] = {
    "None": 0.0,
    "Low": 2.5,
    "Medium": 5.5,
    "High": 8.0,
    "Critical": 9.5,
}

# Risk-level thresholds, expressed as the minimum score (inclusive) for each
# level. Ordered from highest to lowest for evaluation. These bounds mirror
# the CVSS band thresholds used by the OpenVAS parser for consistency.
RISK_LEVEL_THRESHOLDS: tuple[tuple[float, RiskLevel], ...] = (
    (9.0, RiskLevel.CRITICAL),
    (7.0, RiskLevel.HIGH),
    (4.0, RiskLevel.MEDIUM),
    (0.0001, RiskLevel.LOW),
    (SCORE_MIN, RiskLevel.INFORMATIONAL),
)

# Bounded influence of how widely a single vulnerability is observed within
# one scan. Each factor is intentionally small relative to the base CVSS
# score so that widespread exposure nudges risk upward without overriding
# the scanner-reported severity.
ASSET_INFLUENCE_STEP = 0.1
ASSET_INFLUENCE_MAX = 1.0
SERVICE_INFLUENCE_STEP = 0.05
SERVICE_INFLUENCE_MAX = 0.5


def clamp_score(score: float) -> float:
    """Clamp a raw score into the supported [SCORE_MIN, SCORE_MAX] bound."""
    return max(SCORE_MIN, min(SCORE_MAX, score))


def base_score_for(severity_score: float, severity_rating: str) -> tuple[float, bool]:
    """Resolve the base score for a vulnerability.

    Uses the scanner-reported CVSS score when available (non-zero). When no
    CVSS score is present, falls back to the standardized severity-rating
    mapping. Returns a tuple of (base_score, cvss_used).
    """
    if severity_score and severity_score > SCORE_MIN:
        return clamp_score(severity_score), True

    return (
        SEVERITY_BASE_SCORES.get(severity_rating, SEVERITY_BASE_SCORES["None"]),
        False,
    )


def asset_influence_bonus(affected_asset_count: int) -> float:
    """Bounded score bonus for a vulnerability affecting multiple assets."""
    additional_assets = max(0, affected_asset_count - 1)
    return min(additional_assets * ASSET_INFLUENCE_STEP, ASSET_INFLUENCE_MAX)


def service_influence_bonus(affected_service_count: int) -> float:
    """Bounded score bonus for a vulnerability affecting multiple services."""
    additional_services = max(0, affected_service_count - 1)
    return min(additional_services * SERVICE_INFLUENCE_STEP, SERVICE_INFLUENCE_MAX)


def risk_level_for(score: float) -> RiskLevel:
    """Map a bounded score to its standardized risk level."""
    for threshold, level in RISK_LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return RiskLevel.INFORMATIONAL
