"""Risk Coordinator: entry point of the Risk Engine.

Given the vulnerability-bearing findings for a single scan, the coordinator
deterministically produces the vulnerability-level, asset-level, and
scan-level risk results. It performs no database access and calls no
external service; every output is a pure function of its input.
"""

import uuid
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from app.core.exceptions import InternalException
from app.models.scan_finding import ScanFinding
from app.risk_engine.aggregator import AggregationResult, aggregate
from app.risk_engine.calculator import (
    VulnerabilityRiskResult,
    calculate_vulnerability_risk,
)
from app.risk_engine.context import build_context


@dataclass(frozen=True)
class FindingRiskResult:
    """Risk result for a single ScanFinding, paired with the finding it scores."""

    finding: ScanFinding
    result: VulnerabilityRiskResult


@dataclass(frozen=True)
class ScanRiskCalculation:
    """Complete deterministic risk calculation output for one scan."""

    finding_results: list[FindingRiskResult]
    asset_results: dict[uuid.UUID, AggregationResult]
    scan_result: AggregationResult


def calculate_scan_risk(findings: Sequence[ScanFinding]) -> ScanRiskCalculation:
    """Calculate vulnerability, asset, and scan risk for one scan's findings.

    Findings without an associated vulnerability (service-only observations)
    carry no risk and are excluded from calculation.

    Args:
        findings: All ScanFinding rows for a single scan, with their
            vulnerability relationship loaded.

    Returns:
        A ScanRiskCalculation with the full breakdown of results.
    """
    vulnerable_findings = [f for f in findings if f.vulnerability_id is not None]

    finding_results: list[FindingRiskResult] = []
    for finding in vulnerable_findings:
        if finding.vulnerability_id is None:
            raise InternalException(
                "Vulnerable finding unexpectedly has no vulnerability_id."
            )
        context = build_context(vulnerable_findings, finding.vulnerability_id)
        result = calculate_vulnerability_risk(
            severity_score=finding.vulnerability.severity_score,
            severity_rating=finding.vulnerability.severity_rating,
            context=context,
        )
        finding_results.append(FindingRiskResult(finding=finding, result=result))

    asset_contributions: dict[uuid.UUID, list[tuple[uuid.UUID, float]]] = defaultdict(
        list
    )
    for finding_result in finding_results:
        vulnerability_id = finding_result.finding.vulnerability_id
        if vulnerability_id is None:
            raise InternalException(
                "Vulnerable finding unexpectedly has no vulnerability_id."
            )
        asset_contributions[finding_result.finding.asset_id].append(
            (vulnerability_id, finding_result.result.score)
        )

    asset_results = {
        asset_id: aggregate(contributions)
        for asset_id, contributions in asset_contributions.items()
    }

    scan_contributions = [
        (asset_id, agg_result.score) for asset_id, agg_result in asset_results.items()
    ]
    scan_result = aggregate(scan_contributions)

    return ScanRiskCalculation(
        finding_results=finding_results,
        asset_results=asset_results,
        scan_result=scan_result,
    )
