import uuid

from app.models.scan_finding import ScanFinding
from app.models.vulnerability import Vulnerability
from app.risk_engine.coordinator import calculate_scan_risk


def _finding_with_vulnerability(
    asset_id, severity_score, severity_rating, service_id=None, vulnerability_id=None
):
    vulnerability_id = vulnerability_id or uuid.uuid4()
    vulnerability = Vulnerability(
        id=vulnerability_id,
        name="Test Vulnerability",
        severity_score=severity_score,
        severity_rating=severity_rating,
    )
    finding = ScanFinding(
        scan_id=uuid.uuid4(),
        asset_id=asset_id,
        vulnerability_id=vulnerability_id,
        service_id=service_id or uuid.uuid4(),
    )
    finding.vulnerability = vulnerability
    return finding


def test_calculate_scan_risk_empty_findings():
    calculation = calculate_scan_risk([])

    assert calculation.finding_results == []
    assert calculation.asset_results == {}
    assert calculation.scan_result.score == 0.0


def test_calculate_scan_risk_excludes_findings_without_vulnerability():
    service_only_finding = ScanFinding(
        scan_id=uuid.uuid4(),
        asset_id=uuid.uuid4(),
        vulnerability_id=None,
        service_id=uuid.uuid4(),
    )
    calculation = calculate_scan_risk([service_only_finding])

    assert calculation.finding_results == []
    assert calculation.scan_result.score == 0.0


def test_calculate_scan_risk_single_finding():
    asset_id = uuid.uuid4()
    finding = _finding_with_vulnerability(asset_id, 6.0, "Medium")

    calculation = calculate_scan_risk([finding])

    assert len(calculation.finding_results) == 1
    assert calculation.asset_results[asset_id].score == 6.0
    assert calculation.scan_result.score == 6.0


def test_calculate_scan_risk_multiple_findings_same_asset_uses_max():
    asset_id = uuid.uuid4()
    low = _finding_with_vulnerability(asset_id, 3.0, "Low")
    high = _finding_with_vulnerability(asset_id, 8.5, "High")

    calculation = calculate_scan_risk([low, high])

    assert calculation.asset_results[asset_id].score == 8.5
    assert calculation.scan_result.score == 8.5


def test_calculate_scan_risk_multiple_assets_scan_uses_max_asset():
    asset_low, asset_high = uuid.uuid4(), uuid.uuid4()
    low = _finding_with_vulnerability(asset_low, 2.0, "Low")
    high = _finding_with_vulnerability(asset_high, 9.5, "Critical")

    calculation = calculate_scan_risk([low, high])

    assert calculation.asset_results[asset_low].score == 2.0
    assert calculation.asset_results[asset_high].score == 9.5
    assert calculation.scan_result.score == 9.5


def test_calculate_scan_risk_shared_vulnerability_across_assets_applies_influence():
    vulnerability_id = uuid.uuid4()
    asset_a, asset_b, asset_c = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    findings = [
        _finding_with_vulnerability(
            asset_a, 5.0, "Medium", vulnerability_id=vulnerability_id
        ),
        _finding_with_vulnerability(
            asset_b, 5.0, "Medium", vulnerability_id=vulnerability_id
        ),
        _finding_with_vulnerability(
            asset_c, 5.0, "Medium", vulnerability_id=vulnerability_id
        ),
    ]

    calculation = calculate_scan_risk(findings)

    # 3 assets -> asset bonus = (3-1)*0.1 = 0.2
    # 3 distinct services, one per finding -> service bonus = (3-1)*0.05 = 0.1
    for finding_result in calculation.finding_results:
        assert finding_result.result.score == 5.3


def test_calculate_scan_risk_is_deterministic():
    asset_id = uuid.uuid4()
    finding = _finding_with_vulnerability(asset_id, 6.0, "Medium")

    first = calculate_scan_risk([finding])
    second = calculate_scan_risk([finding])

    assert first.scan_result.score == second.scan_result.score
    assert first.asset_results[asset_id].score == second.asset_results[asset_id].score
