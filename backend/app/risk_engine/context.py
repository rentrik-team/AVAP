"""Context Engine: derives contextual scoring factors from already-loaded data.

The Context Engine never queries the database directly. It operates purely
on ScanFinding rows already loaded by the Service layer, keeping the Risk
Engine deterministic and independent of persistence concerns.
"""

import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from app.models.scan_finding import ScanFinding


@dataclass(frozen=True)
class RiskContext:
    """Contextual factors influencing a single vulnerability's risk score."""

    affected_asset_count: int
    affected_service_count: int


def build_context(
    findings: Sequence[ScanFinding], vulnerability_id: uuid.UUID
) -> RiskContext:
    """Compute how widely a vulnerability is observed within a set of findings.

    Args:
        findings: All vulnerability-bearing findings within the calculation scope
            (typically one scan).
        vulnerability_id: The vulnerability whose exposure is being measured.

    Returns:
        A RiskContext with the distinct affected asset and service counts.
    """
    matching = [f for f in findings if f.vulnerability_id == vulnerability_id]
    asset_ids = {f.asset_id for f in matching}
    service_ids = {f.service_id for f in matching if f.service_id is not None}
    return RiskContext(
        affected_asset_count=len(asset_ids),
        affected_service_count=len(service_ids),
    )
