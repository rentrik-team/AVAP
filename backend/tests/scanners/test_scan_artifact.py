import uuid
from datetime import datetime
from pathlib import Path

from app.core.enums import ExecutionStatus, ScannerType
from app.scanners.scan_artifact import ScanArtifact


def test_scan_artifact_creation():
    """Verify that ScanArtifact initializes with default and provided values."""
    scan_id = uuid.uuid4()
    artifact = ScanArtifact(
        scan_id=scan_id,
        scanner_type=ScannerType.NMAP,
        execution_status=ExecutionStatus.SUCCESS,
        exit_code=0,
        execution_duration_seconds=5.2,
        stdout="nmap scan stdout",
        stderr="nmap scan stderr",
        output_path=Path("nonexistent_nmap.xml"),
        metadata={"hosts_up": 1},
    )

    assert artifact.scan_id == scan_id
    assert artifact.scanner_type == ScannerType.NMAP
    assert artifact.execution_status == ExecutionStatus.SUCCESS
    assert artifact.exit_code == 0
    assert artifact.execution_duration_seconds == 5.2
    assert artifact.stdout == "nmap scan stdout"
    assert artifact.stderr == "nmap scan stderr"
    assert artifact.output_path == Path("nonexistent_nmap.xml")
    assert artifact.metadata == {"hosts_up": 1}
    assert isinstance(artifact.artifact_id, uuid.UUID)
    assert isinstance(artifact.created_at, datetime)
    assert artifact.is_successful is True
    assert artifact.has_output is False  # Path does not exist


def test_scan_artifact_failure_states():
    """Verify is_successful helper for different ExecutionStatus values."""
    for status in [
        ExecutionStatus.FAILED,
        ExecutionStatus.TIMEOUT,
        ExecutionStatus.ERROR,
    ]:
        artifact = ScanArtifact(execution_status=status)
        assert artifact.is_successful is False
