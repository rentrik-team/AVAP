from app.core.enums import RiskLevel
from app.risk_engine.calculator import calculate_vulnerability_risk
from app.risk_engine.context import RiskContext


def test_calculate_uses_cvss_score_directly():
    context = RiskContext(affected_asset_count=1, affected_service_count=1)
    result = calculate_vulnerability_risk(7.5, "High", context)

    assert result.score == 7.5
    assert result.level == RiskLevel.HIGH
    assert result.supporting_factors["cvss_used"] is True
    assert result.supporting_factors["base_score"] == 7.5


def test_calculate_missing_cvss_uses_severity_fallback():
    context = RiskContext(affected_asset_count=1, affected_service_count=1)
    result = calculate_vulnerability_risk(0.0, "Medium", context)

    assert result.score == 5.5
    assert result.level == RiskLevel.MEDIUM
    assert result.supporting_factors["cvss_used"] is False


def test_calculate_applies_asset_and_service_influence():
    context = RiskContext(affected_asset_count=6, affected_service_count=3)
    result = calculate_vulnerability_risk(5.0, "Medium", context)

    # base 5.0 + asset bonus (5 additional * 0.1 = 0.5) + service bonus (2 * 0.05 = 0.1)
    assert result.score == 5.6
    assert result.supporting_factors["asset_influence_bonus"] == 0.5
    assert result.supporting_factors["service_influence_bonus"] == 0.1


def test_calculate_clamps_final_score_at_upper_bound():
    context = RiskContext(affected_asset_count=50, affected_service_count=50)
    result = calculate_vulnerability_risk(9.8, "Critical", context)

    assert result.score == 10.0
    assert result.level == RiskLevel.CRITICAL


def test_calculate_informational_zero_score():
    context = RiskContext(affected_asset_count=1, affected_service_count=1)
    result = calculate_vulnerability_risk(0.0, "None", context)

    assert result.score == 0.0
    assert result.level == RiskLevel.INFORMATIONAL


def test_calculate_is_deterministic():
    context = RiskContext(affected_asset_count=3, affected_service_count=2)
    first = calculate_vulnerability_risk(6.4, "Medium", context)
    second = calculate_vulnerability_risk(6.4, "Medium", context)

    assert first.score == second.score
    assert first.level == second.level
    assert first.supporting_factors == second.supporting_factors
