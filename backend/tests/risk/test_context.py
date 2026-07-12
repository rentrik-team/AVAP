import uuid

from app.models.scan_finding import ScanFinding
from app.risk_engine.context import build_context


def _finding(asset_id, vulnerability_id, service_id=None):
    return ScanFinding(
        scan_id=uuid.uuid4(),
        asset_id=asset_id,
        vulnerability_id=vulnerability_id,
        service_id=service_id,
    )


def test_build_context_counts_distinct_assets_and_services():
    vuln_id = uuid.uuid4()
    other_vuln_id = uuid.uuid4()
    asset_a, asset_b = uuid.uuid4(), uuid.uuid4()
    service_a, service_b = uuid.uuid4(), uuid.uuid4()

    findings = [
        _finding(asset_a, vuln_id, service_a),
        _finding(asset_b, vuln_id, service_b),
        _finding(asset_a, other_vuln_id, service_a),  # different vulnerability, ignored
    ]

    context = build_context(findings, vuln_id)

    assert context.affected_asset_count == 2
    assert context.affected_service_count == 2


def test_build_context_deduplicates_repeated_asset():
    vuln_id = uuid.uuid4()
    asset_a = uuid.uuid4()
    service_a, service_b = uuid.uuid4(), uuid.uuid4()

    findings = [
        _finding(asset_a, vuln_id, service_a),
        _finding(asset_a, vuln_id, service_b),
    ]

    context = build_context(findings, vuln_id)

    assert context.affected_asset_count == 1
    assert context.affected_service_count == 2


def test_build_context_ignores_null_service():
    vuln_id = uuid.uuid4()
    asset_a = uuid.uuid4()

    findings = [_finding(asset_a, vuln_id, service_id=None)]

    context = build_context(findings, vuln_id)

    assert context.affected_asset_count == 1
    assert context.affected_service_count == 0


def test_build_context_no_matching_findings():
    context = build_context([], uuid.uuid4())
    assert context.affected_asset_count == 0
    assert context.affected_service_count == 0
