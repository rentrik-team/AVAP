"""Full-lifecycle Module 10 integration test: Target creation -> Scan
creation -> Inventory processing -> Risk calculation -> AI recommendation
generation (fake provider boundary) -> Report generation -> Audit API
retrieval.

Exercises the real repository/service/API boundaries end to end; no part
of the audit subsystem is mocked.
"""

import uuid

from fastapi.testclient import TestClient

from app.ai.provider import AIProviderResponse
from app.core.config import Settings
from app.core.enums import RiskScope
from app.repositories.ai_recommendation_repository import AIRecommendationRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.network_service_repository import NetworkServiceRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.risk_repository import RiskRepository
from app.repositories.scan_finding_repository import ScanFindingRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.target_repository import TargetRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.services.audit_service import AuditService
from app.services.inventory_service import InventoryService
from app.services.report_service import ReportService


class _FakeProviderBoundaryManager:
    def resolve_provider_name(self):
        return "openrouter"

    def resolve_model_name(self):
        return "fake-integration-model"

    def generate(self, prompt):
        content = (
            '{"summary": "Upgrade the vulnerable service.", '
            '"explanation": "The detected version is affected by known CVEs.", '
            '"remediation_steps": ["Apply the latest security patch."], '
            '"validation_steps": ["Confirm the updated version."], '
            '"cautions": ["Restart during a maintenance window."]}'
        )
        return AIProviderResponse(
            content=content, provider="openrouter", model="fake-integration-model"
        )


def test_full_lifecycle_produces_expected_audit_trail(
    client: TestClient, db_session, tmp_path
):
    # --- Module 01: create a target through the real API ---
    target_response = client.post("/api/v1/targets", json={"target": "203.0.113.150"})
    assert target_response.status_code == 201
    target_id = target_response.json()["data"]["id"]

    # --- Module 02: create a scan through the real API ---
    # No scanner engine is wired for this test environment (no real Nmap/
    # OpenVAS binaries available); override with scanner_engine=None so the
    # scan is created and stays PENDING without dispatching a real process,
    # matching this suite's existing convention for scan API tests.
    from app.api.routes.v1.scans import get_scan_service
    from app.main import app
    from app.services.audit_service import AuditService as _AuditServiceForScan
    from app.services.scan_service import ScanService

    def override_scan_service():
        return ScanService(
            scan_repository=ScanRepository(db_session),
            target_repository=TargetRepository(db_session),
            audit_service=_AuditServiceForScan(AuditRepository(db_session)),
            scanner_engine=None,
        )

    app.dependency_overrides[get_scan_service] = override_scan_service
    try:
        scan_response = client.post(
            "/api/v1/scans", json={"target_id": target_id, "scan_profile": "full"}
        )
        assert scan_response.status_code == 201
        scan_id = uuid.UUID(scan_response.json()["data"]["scan_id"])
    finally:
        app.dependency_overrides.pop(get_scan_service, None)

    # --- Module 05: process an assessment package via InventoryService ---
    from app.parsers.models import (
        AssessmentPackage,
        ParsedHost,
        ParsedService,
        ParsedVulnerability,
    )

    audit_service = AuditService(AuditRepository(db_session))
    inventory_service = InventoryService(
        db_session,
        AssetRepository(db_session),
        VulnerabilityRepository(db_session),
        ScanRepository(db_session),
        audit_service,
    )
    vuln = ParsedVulnerability(
        name="Outdated Service",
        severity_score=8.0,
        severity_rating="High",
        cve="CVE-2024-8100",
    )
    service = ParsedService(
        port=443, protocol="tcp", service_name="https", vulnerabilities=[vuln]
    )
    host = ParsedHost(ipv4="203.0.113.150", services=[service])
    package = AssessmentPackage(
        scan_id=scan_id, scanner_type="OPENVAS", parsed_hosts=[host]
    )
    inventory_service.process_assessment_package(package)

    # --- Module 06: calculate risk through the real API ---
    risk_response = client.post(f"/api/v1/risk/scans/{scan_id}/calculate")
    assert risk_response.status_code == 200

    risk_repository = RiskRepository(db_session)
    vulnerability_risk = risk_repository.get_by_scan_and_scope(
        scan_id, RiskScope.VULNERABILITY
    )[0]

    # --- Module 07: generate an AI recommendation via the real API ---
    from app.api.routes.v1.ai import get_ai_service
    from app.main import app

    def override_ai_service():
        from app.services.ai_service import AIService

        return AIService(
            session=db_session,
            ai_recommendation_repository=AIRecommendationRepository(db_session),
            risk_repository=risk_repository,
            vulnerability_repository=VulnerabilityRepository(db_session),
            network_service_repository=NetworkServiceRepository(db_session),
            audit_service=audit_service,
            ai_manager=_FakeProviderBoundaryManager(),
        )

    app.dependency_overrides[get_ai_service] = override_ai_service
    try:
        ai_response = client.post(
            f"/api/v1/ai/recommendations/{vulnerability_risk.id}/generate"
        )
        assert ai_response.status_code == 200
    finally:
        app.dependency_overrides.pop(get_ai_service, None)

    # --- Module 08: generate a report via the real API ---
    from app.api.routes.v1.reports import get_report_service

    def override_report_service():
        return ReportService(
            session=db_session,
            report_repository=ReportRepository(db_session),
            scan_repository=ScanRepository(db_session),
            risk_repository=risk_repository,
            asset_repository=AssetRepository(db_session),
            vulnerability_repository=VulnerabilityRepository(db_session),
            network_service_repository=NetworkServiceRepository(db_session),
            scan_finding_repository=ScanFindingRepository(db_session),
            ai_recommendation_repository=AIRecommendationRepository(db_session),
            audit_service=audit_service,
            settings=Settings(_env_file=None, report_output_directory=str(tmp_path)),
        )

    app.dependency_overrides[get_report_service] = override_report_service
    try:
        report_response = client.post("/api/v1/reports", json={"scan_id": str(scan_id)})
        assert report_response.status_code == 201
        report_id = report_response.json()["data"]["id"]
    finally:
        app.dependency_overrides.pop(get_report_service, None)

    # --- Module 10: verify the resulting audit trail via the real API ---
    all_events_response = client.get("/api/v1/audit", params={"limit": 50})
    all_events = all_events_response.json()["data"]["events"]

    event_types = [e["event_type"] for e in all_events]
    assert "TARGET_CREATED" in event_types
    assert "SCAN_CREATED" in event_types
    assert "INVENTORY_PROCESSED" in event_types
    assert "RISK_CALCULATION_COMPLETED" in event_types
    assert "AI_RECOMMENDATION_GENERATED" in event_types
    assert "REPORT_GENERATED" in event_types

    # Deterministic ordering: newest first.
    occurred_ats = [e["occurred_at"] for e in all_events]
    assert occurred_ats == sorted(occurred_ats, reverse=True)

    # Every event succeeded; no false or unexpected failures in this
    # golden-path lifecycle.
    assert all(e["outcome"] == "SUCCESS" for e in all_events)

    # Resource IDs correlate correctly.
    scan_events = [e for e in all_events if e["scan_id"] == str(scan_id)]
    assert len(scan_events) >= 3  # inventory + risk + report at minimum

    report_event = next(e for e in all_events if e["event_type"] == "REPORT_GENERATED")
    assert report_event["resource_id"] == report_id

    # Actor semantics: HTTP-triggered actions resolve to ANONYMOUS.
    target_created_event = next(
        e for e in all_events if e["event_type"] == "TARGET_CREATED"
    )
    assert target_created_event["actor_type"] == "ANONYMOUS"
    assert target_created_event["actor_id"] is None

    # --- No forbidden content anywhere in the audit trail ---
    import json

    serialized = json.dumps(all_events)
    # Actual AI recommendation content (never audited).
    forbidden_fragments = [
        "Upgrade the vulnerable service",
        "Apply the latest security patch",
        "Confirm the updated version",
        "Restart during a maintenance window",
        str(tmp_path),
        ".pdf",
        "api_key",
        "openrouter_api_key",
        "password",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in serialized, f"Forbidden content leaked: {fragment}"

    # Provider/model/prompt-version identifiers ARE legitimate metadata
    # (not the prompt/response content itself).
    ai_event = next(
        e for e in all_events if e["event_type"] == "AI_RECOMMENDATION_GENERATED"
    )
    assert ai_event["event_metadata"]["provider"] == "openrouter"
    assert ai_event["event_metadata"]["prompt_version"]
    for forbidden_key in (
        "summary",
        "explanation",
        "remediation_steps",
        "validation_steps",
        "cautions",
    ):
        assert forbidden_key not in ai_event["event_metadata"]
