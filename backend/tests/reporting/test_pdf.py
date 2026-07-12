import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.core.enums import RiskLevel, ScanStatus, TargetType
from app.reporting.pdf import render_pdf
from app.schemas.report import (
    AffectedService,
    AssetSummary,
    ExecutiveSummary,
    FindingDetail,
    RemediationGuidance,
    ReportData,
    ReportMetadata,
    SeverityDistribution,
)

PDF_SIGNATURE = b"%PDF-"


def _metadata(**overrides):
    defaults = {
        "scan_id": uuid.uuid4(),
        "target": "192.168.1.1",
        "target_type": TargetType.IPV4,
        "scan_status": ScanStatus.COMPLETED,
        "scan_started_at": datetime.now(UTC),
        "scan_completed_at": datetime.now(UTC),
        "generated_at": datetime.now(UTC),
        "report_template_version": "1.0.0",
        "risk_calculation_version": "1.0.0",
    }
    defaults.update(overrides)
    return ReportMetadata(**defaults)


def _finding(**overrides):
    defaults = {
        "vulnerability_id": uuid.uuid4(),
        "vulnerability_name": "Outdated OpenSSH",
        "cve": "CVE-2024-1234",
        "description": "A description of the vulnerability.",
        "severity_rating": "High",
        "severity_score": 7.5,
        "risk_score": 7.8,
        "risk_level": RiskLevel.HIGH,
        "asset_ipv4": "192.168.1.1",
        "asset_hostname": "host.local",
        "affected_service": AffectedService(
            port=22,
            protocol="tcp",
            service_name="ssh",
            product="OpenSSH",
            version="7.4",
        ),
        "remediation": None,
    }
    defaults.update(overrides)
    return FindingDetail(**defaults)


def _report_data(findings=None, assets=None):
    findings = findings if findings is not None else [_finding()]
    assets = (
        assets
        if assets is not None
        else [
            AssetSummary(
                asset_id=uuid.uuid4(),
                ipv4="192.168.1.1",
                hostname="host.local",
                operating_system="Linux",
                risk_score=7.8,
                risk_level=RiskLevel.HIGH,
                vulnerability_count=len(findings),
            )
        ]
    )
    severity = SeverityDistribution(high=len(findings))
    exec_summary = ExecutiveSummary(
        overall_risk_score=7.8,
        overall_risk_level=RiskLevel.HIGH,
        total_assets=len(assets),
        total_vulnerabilities=len(findings),
        severity_distribution=severity,
    )
    return ReportData(
        metadata=_metadata(),
        executive_summary=exec_summary,
        assets=assets,
        findings=findings,
    )


def _remediation(**overrides):
    defaults = {
        "summary": "Upgrade required.",
        "explanation": "This version is vulnerable to remote code execution.",
        "remediation_steps": ["Apply the vendor patch.", "Restart the service."],
        "validation_steps": ["Confirm the version banner updated."],
        "cautions": ["Perform during a maintenance window."],
        "provider": "openrouter",
        "model": "test-model",
        "generated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return RemediationGuidance(**defaults)


# --- Valid rendering ---


def test_render_pdf_produces_valid_signature(tmp_path: Path):
    output = tmp_path / "report.pdf"
    render_pdf(_report_data(), output)

    assert output.exists()
    assert output.stat().st_size > 0
    assert output.read_bytes()[:5] == PDF_SIGNATURE


def test_render_pdf_executive_summary_and_risk_values_present(tmp_path: Path):
    output = tmp_path / "report.pdf"
    render_pdf(_report_data(), output)
    assert output.stat().st_size > 0


def test_render_pdf_with_remediation(tmp_path: Path):
    output = tmp_path / "report.pdf"
    finding = _finding(remediation=_remediation())
    render_pdf(_report_data(findings=[finding]), output)
    assert output.read_bytes()[:5] == PDF_SIGNATURE


def test_render_pdf_missing_remediation_handled(tmp_path: Path):
    output = tmp_path / "report.pdf"
    finding = _finding(remediation=None)
    render_pdf(_report_data(findings=[finding]), output)
    assert output.read_bytes()[:5] == PDF_SIGNATURE


def test_render_pdf_empty_assets_section(tmp_path: Path):
    output = tmp_path / "report.pdf"
    render_pdf(_report_data(assets=[]), output)
    assert output.read_bytes()[:5] == PDF_SIGNATURE


# --- Layout safety with adversarial/oversized content ---


def test_render_pdf_long_vulnerability_name(tmp_path: Path):
    output = tmp_path / "report.pdf"
    # At the contract's own bound (200 chars) — the longest a name can ever be.
    finding = _finding(vulnerability_name=("Vulnerability " + "X" * 500)[:200])
    render_pdf(_report_data(findings=[finding]), output)
    assert output.read_bytes()[:5] == PDF_SIGNATURE


def test_render_pdf_long_description(tmp_path: Path):
    output = tmp_path / "report.pdf"
    # At the contract's own bound (3000 chars) — the longest a description can ever be.
    finding = _finding(description=("Detailed description. " * 300)[:3000])
    render_pdf(_report_data(findings=[finding]), output)
    assert output.read_bytes()[:5] == PDF_SIGNATURE


def test_render_pdf_long_service_product_version(tmp_path: Path):
    output = tmp_path / "report.pdf"
    service = AffectedService(
        port=443,
        protocol="tcp",
        service_name="https",
        product="Product" + "Z" * 90,
        version="Version" + "9" * 40,
    )
    finding = _finding(affected_service=service)
    render_pdf(_report_data(findings=[finding]), output)
    assert output.read_bytes()[:5] == PDF_SIGNATURE


def test_render_pdf_long_remediation_steps(tmp_path: Path):
    output = tmp_path / "report.pdf"
    remediation = _remediation(
        remediation_steps=["Step " + "A" * 400 for _ in range(15)]
    )
    finding = _finding(remediation=remediation)
    render_pdf(_report_data(findings=[finding]), output)
    assert output.read_bytes()[:5] == PDF_SIGNATURE


def test_render_pdf_multi_page_many_findings(tmp_path: Path):
    output = tmp_path / "report.pdf"
    findings = [
        _finding(
            vulnerability_id=uuid.uuid4(),
            vulnerability_name=f"Vulnerability {i}",
            cve=f"CVE-2024-{1000 + i}",
            remediation=_remediation(),
        )
        for i in range(40)
    ]
    render_pdf(_report_data(findings=findings), output)
    assert output.read_bytes()[:5] == PDF_SIGNATURE
    assert output.stat().st_size > 5000


# --- Untrusted text / markup injection safety ---


@pytest.mark.parametrize(
    "payload",
    [
        "<font color=red size=40>Injected</font>",
        '<img src="http://evil.example/x.png" onerror="alert(1)"/>',
        '<a href="http://evil.example">click me</a>',
        "<br/><br/><malformed<<< tag",
        "<" * 5000,
    ],
)
def test_render_pdf_handles_markup_injection_payloads(tmp_path: Path, payload):
    output = tmp_path / "report.pdf"
    finding = _finding(
        vulnerability_name=payload[:200],
        description=payload[:3000],
        remediation=_remediation(
            summary=payload[:500],
            explanation=payload[:4000],
            remediation_steps=[payload[:500]],
        ),
    )
    render_pdf(_report_data(findings=[finding]), output)
    assert output.read_bytes()[:5] == PDF_SIGNATURE
