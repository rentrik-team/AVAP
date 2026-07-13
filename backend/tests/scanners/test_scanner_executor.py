import subprocess
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.enums import ExecutionStatus, ScannerType
from app.core.exceptions import ScannerExecutionException, ScannerTimeoutException
from app.scanners.scanner_executor import ScannerExecutor


def test_scanner_executor_validation():
    executor = ScannerExecutor()

    # Reject non-whitelisted executable
    with pytest.raises(ScannerExecutionException) as exc:
        executor.run_scanner(
            scanner_type=ScannerType.NMAP,
            cmd_args=["ping", "127.0.0.1"],
            scan_id=uuid.uuid4(),
        )
    assert "Unauthorized executable" in str(exc.value)

    # Reject empty command list
    with pytest.raises(ScannerExecutionException):
        executor.run_scanner(
            scanner_type=ScannerType.NMAP, cmd_args=[], scan_id=uuid.uuid4()
        )


@patch("subprocess.Popen")
def test_scanner_executor_success(mock_popen):
    # Mock communication success
    mock_process = MagicMock()
    mock_process.communicate.return_value = ("nmap output", "no errors")
    mock_process.returncode = 0
    mock_popen.return_value = mock_process

    executor = ScannerExecutor()
    scan_id = uuid.uuid4()
    output_path = Path("test_output.xml")

    artifact = executor.run_scanner(
        scanner_type=ScannerType.NMAP,
        cmd_args=["nmap", "127.0.0.1"],
        scan_id=scan_id,
        output_path=output_path,
        timeout=10,
    )

    assert artifact.scan_id == scan_id
    assert artifact.scanner_type == ScannerType.NMAP
    assert artifact.execution_status == ExecutionStatus.SUCCESS
    assert artifact.exit_code == 0
    assert artifact.stdout == "nmap output"
    assert artifact.stderr == "no errors"
    assert artifact.output_path == output_path
    assert artifact.execution_duration_seconds >= 0.0


@patch("subprocess.Popen")
def test_scanner_executor_failure_exit_code(mock_popen):
    # Mock process returning non-zero exit code
    mock_process = MagicMock()
    mock_process.communicate.return_value = ("", "nmap failed execution")
    mock_process.returncode = 1
    mock_popen.return_value = mock_process

    executor = ScannerExecutor()
    scan_id = uuid.uuid4()

    artifact = executor.run_scanner(
        scanner_type=ScannerType.NMAP, cmd_args=["nmap", "127.0.0.1"], scan_id=scan_id
    )

    assert artifact.execution_status == ExecutionStatus.FAILED
    assert artifact.exit_code == 1
    assert artifact.stderr == "nmap failed execution"


@patch("subprocess.Popen")
def test_scanner_executor_timeout(mock_popen):
    # Mock timeout exception during communicate
    mock_process = MagicMock()
    mock_process.communicate.side_effect = [
        subprocess.TimeoutExpired(cmd="nmap", timeout=5),
        ("timeout partial output", "timeout partial err"),
    ]
    mock_process.returncode = -9  # typical killed process code
    mock_popen.return_value = mock_process

    executor = ScannerExecutor()
    scan_id = uuid.uuid4()

    with pytest.raises(ScannerTimeoutException) as exc:
        executor.run_scanner(
            scanner_type=ScannerType.NMAP,
            cmd_args=["nmap", "127.0.0.1"],
            scan_id=scan_id,
            timeout=5,
        )
    assert "exceeded timeout of 5 seconds" in str(exc.value)

    mock_process.kill.assert_called_once()
