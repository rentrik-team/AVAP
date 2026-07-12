import uuid

from app.core.enums import RiskLevel
from app.risk_engine.aggregator import aggregate


def test_aggregate_empty_contributions_returns_zero():
    result = aggregate([])

    assert result.score == 0.0
    assert result.level == RiskLevel.INFORMATIONAL
    assert result.supporting_factors["contributing_count"] == 0
    assert result.supporting_factors["contributing_entity_id"] is None


def test_aggregate_single_contribution():
    entity_id = uuid.uuid4()
    result = aggregate([(entity_id, 6.5)])

    assert result.score == 6.5
    assert result.level == RiskLevel.MEDIUM
    assert result.supporting_factors["contributing_entity_id"] == str(entity_id)
    assert result.supporting_factors["contributing_count"] == 1


def test_aggregate_uses_maximum_of_multiple_contributions():
    low_id, high_id, mid_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    result = aggregate([(low_id, 2.0), (high_id, 9.2), (mid_id, 5.0)])

    assert result.score == 9.2
    assert result.level == RiskLevel.CRITICAL
    assert result.supporting_factors["contributing_entity_id"] == str(high_id)
    assert result.supporting_factors["contributing_count"] == 3


def test_aggregate_method_is_recorded_for_explainability():
    result = aggregate([(uuid.uuid4(), 1.0)])
    assert result.supporting_factors["aggregation_method"] == "maximum"
