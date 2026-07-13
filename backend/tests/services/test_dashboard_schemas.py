import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.core.enums import RiskLevel, ScanStatus, TargetType
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    RecentAsset,
    RecentScan,
    TopRiskAsset,
)


def _valid_summary_kwargs(**overrides):
    defaults = {
        "generated_at": datetime.now(UTC),
        "total_targets": 1,
        "total_scans": 1,
        "total_assets": 1,
        "unique_vulnerability_count": 1,
        "critical_vulnerability_count": 0,
        "total_reports_generated": 0,
        "overall_risk_score": 5.0,
        "overall_risk_level": RiskLevel.MEDIUM,
        "high_risk_asset_count": 0,
    }
    defaults.update(overrides)
    return defaults


def test_valid_summary_constructs():
    summary = DashboardSummaryResponse(**_valid_summary_kwargs())
    assert summary.total_scans == 1


def test_empty_state_summary_constructs():
    summary = DashboardSummaryResponse(
        **_valid_summary_kwargs(
            total_targets=0,
            total_scans=0,
            total_assets=0,
            unique_vulnerability_count=0,
            overall_risk_score=0.0,
            overall_risk_level=RiskLevel.INFORMATIONAL,
        )
    )
    assert summary.total_scans == 0
    assert summary.overall_risk_level == RiskLevel.INFORMATIONAL


def test_negative_count_rejected():
    with pytest.raises(ValidationError):
        DashboardSummaryResponse(**_valid_summary_kwargs(total_scans=-1))


def test_risk_score_above_ten_rejected():
    with pytest.raises(ValidationError):
        DashboardSummaryResponse(**_valid_summary_kwargs(overall_risk_score=10.1))


def test_risk_score_below_zero_rejected():
    with pytest.raises(ValidationError):
        DashboardSummaryResponse(**_valid_summary_kwargs(overall_risk_score=-0.1))


def test_invalid_risk_level_enum_rejected():
    with pytest.raises(ValidationError):
        DashboardSummaryResponse(
            **_valid_summary_kwargs(overall_risk_level="NOT_A_LEVEL")
        )


def test_invalid_uuid_rejected_on_top_risk_asset():
    with pytest.raises(ValidationError):
        TopRiskAsset(
            asset_id="not-a-uuid",
            ipv4="10.0.0.1",
            hostname=None,
            risk_score=5.0,
            risk_level=RiskLevel.MEDIUM,
        )


def test_recent_asset_requires_valid_uuid_and_datetime():
    asset = RecentAsset(
        asset_id=uuid.uuid4(),
        ipv4="10.0.0.1",
        hostname=None,
        discovered_at=datetime.now(UTC),
    )
    assert asset.hostname is None
    with pytest.raises(ValidationError):
        RecentAsset(
            asset_id=uuid.uuid4(),
            ipv4="10.0.0.1",
            hostname=None,
            discovered_at="not-a-datetime",
        )


def test_recent_scan_invalid_status_rejected():
    with pytest.raises(ValidationError):
        RecentScan(
            scan_id=uuid.uuid4(),
            target="10.0.0.1",
            target_type=TargetType.IPV4,
            status="NOT_A_STATUS",
        )


def test_recent_scan_negative_duration_rejected():
    with pytest.raises(ValidationError):
        RecentScan(
            scan_id=uuid.uuid4(),
            target="10.0.0.1",
            target_type=TargetType.IPV4,
            status=ScanStatus.COMPLETED,
            execution_duration_seconds=-5.0,
        )
