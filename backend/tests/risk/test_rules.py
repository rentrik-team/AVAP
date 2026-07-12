import pytest

from app.core.enums import RiskLevel
from app.risk_engine import rules

# --- base_score_for: CVSS handling ---


def test_base_score_uses_cvss_when_available():
    score, cvss_used = rules.base_score_for(severity_score=7.5, severity_rating="High")
    assert score == 7.5
    assert cvss_used is True


def test_base_score_clamps_cvss_to_bounds():
    score, cvss_used = rules.base_score_for(
        severity_score=15.0, severity_rating="Critical"
    )
    assert score == rules.SCORE_MAX
    assert cvss_used is True


@pytest.mark.parametrize(
    "rating,expected",
    [
        ("None", 0.0),
        ("Low", 2.5),
        ("Medium", 5.5),
        ("High", 8.0),
        ("Critical", 9.5),
    ],
)
def test_base_score_fallback_severity_mapping(rating, expected):
    score, cvss_used = rules.base_score_for(severity_score=0.0, severity_rating=rating)
    assert score == expected
    assert cvss_used is False


def test_base_score_fallback_unrecognized_rating_defaults_to_none():
    score, cvss_used = rules.base_score_for(
        severity_score=0.0, severity_rating="Unknown"
    )
    assert score == 0.0
    assert cvss_used is False


# --- clamp_score ---


def test_clamp_score_lower_bound():
    assert rules.clamp_score(-5.0) == rules.SCORE_MIN


def test_clamp_score_upper_bound():
    assert rules.clamp_score(50.0) == rules.SCORE_MAX


def test_clamp_score_within_bounds_unchanged():
    assert rules.clamp_score(5.5) == 5.5


# --- risk_level_for: threshold boundaries ---


@pytest.mark.parametrize(
    "score,expected_level",
    [
        (0.0, RiskLevel.INFORMATIONAL),
        (0.05, RiskLevel.LOW),
        (3.99, RiskLevel.LOW),
        (4.0, RiskLevel.MEDIUM),
        (6.99, RiskLevel.MEDIUM),
        (7.0, RiskLevel.HIGH),
        (8.99, RiskLevel.HIGH),
        (9.0, RiskLevel.CRITICAL),
        (10.0, RiskLevel.CRITICAL),
    ],
)
def test_risk_level_thresholds(score, expected_level):
    assert rules.risk_level_for(score) == expected_level


# --- Asset / service influence bonuses ---


def test_asset_influence_bonus_single_asset_no_bonus():
    assert rules.asset_influence_bonus(1) == 0.0


def test_asset_influence_bonus_scales_and_caps():
    assert rules.asset_influence_bonus(2) == pytest.approx(0.1)
    assert rules.asset_influence_bonus(5) == pytest.approx(0.4)
    assert rules.asset_influence_bonus(100) == rules.ASSET_INFLUENCE_MAX


def test_service_influence_bonus_single_service_no_bonus():
    assert rules.service_influence_bonus(1) == 0.0


def test_service_influence_bonus_scales_and_caps():
    assert rules.service_influence_bonus(2) == pytest.approx(0.05)
    assert rules.service_influence_bonus(100) == rules.SERVICE_INFLUENCE_MAX


def test_asset_influence_bonus_zero_count_no_bonus():
    """Defensive: zero affected assets never produces a negative bonus."""
    assert rules.asset_influence_bonus(0) == 0.0
