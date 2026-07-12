"""Risk Aggregation Engine: rolls up child risk scores into a parent scope.

The platform uses a single, consistent aggregation rule at every level
(asset, scan, assessment): the parent's risk score is the maximum score
among its children. This "worst case drives the aggregate" rule is
deterministic, requires no additional tunable constants, and is trivially
explainable: the parent is only ever as safe as its riskiest component.
"""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.core.enums import RiskLevel
from app.risk_engine import rules


@dataclass(frozen=True)
class AggregationResult:
    """Deterministic aggregation result for a parent risk scope."""

    score: float
    level: RiskLevel
    supporting_factors: dict[str, Any]


def aggregate(contributions: Sequence[tuple[uuid.UUID, float]]) -> AggregationResult:
    """Aggregate child risk scores into a single parent risk score.

    Args:
        contributions: Sequence of (entity_id, score) pairs for the direct
            children of the scope being aggregated (e.g. an asset's
            vulnerability scores, or a scan's asset scores). An empty
            sequence represents a scope with no assessed risk.

    Returns:
        An AggregationResult using the maximum child score, with the
        contributing entity recorded for explainability.
    """
    if not contributions:
        return AggregationResult(
            score=rules.SCORE_MIN,
            level=rules.risk_level_for(rules.SCORE_MIN),
            supporting_factors={
                "aggregation_method": "maximum",
                "contributing_count": 0,
                "contributing_entity_id": None,
            },
        )

    contributing_entity_id, max_score = max(contributions, key=lambda item: item[1])
    level = rules.risk_level_for(max_score)

    return AggregationResult(
        score=max_score,
        level=level,
        supporting_factors={
            "aggregation_method": "maximum",
            "contributing_count": len(contributions),
            "contributing_entity_id": str(contributing_entity_id),
        },
    )
