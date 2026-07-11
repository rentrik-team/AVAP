import pytest
from unittest.mock import MagicMock, patch
import subprocess
import uuid

from app.core.enums import ScannerType, ScanProfile
from app.core.exceptions import ValidationException, ScannerExecutionException
from app.scanners.execution_validator import ExecutionValidator
from app.scanners.adapters.nmap_adapter import NmapAdapter
from app.scanners.scanner_executor import ScannerExecutor


def test_security_target_validation_metacharacters():
    """Verify that ExecutionValidator blocks shell metacharacters in targets."""
    validator = ExecutionValidator()
    
    malicious_targets = [
        "127.0.0.1; rm -rf /",
        "127.0.0.1 && cat /etc/passwd",
        "example.com | netcat -l -p 4444",
        "$(whoami).example.com",
        "example.com`id`",
        "127.0.0.1\n/bin/sh",
    ]
    
    for target in malicious_targets:
        with pytest.raises(ValidationException) as exc:
            validator.validate_request(target, ScannerType.NMAP, ScanProfile.DISCOVERY)
        # Should be caught either by format validation or explicit shell char check
        assert any(
            phrase in str(exc.value) 
            for phrase in ["Invalid target format", "contains disallowed shell characters"]
        )


def test_security_option_injection_prevention():
    """Verify that NmapAdapter blocks arguments starting with '-' to prevent option injection."""
    adapter = NmapAdapter()
    
    injection_targets = [
        "-sS",
        "--stylesheet",
        "-iL /etc/passwd",
    ]
    
    for target in injection_targets:
        with pytest.raises(ScannerExecutionException) as exc:
            adapter.build_command(target, ScanProfile.PORT_SCAN, "output.xml")
        assert "cannot start with a hyphen" in str(exc.value)


@patch("subprocess.Popen")
def test_security_shell_false_enforcement(mock_popen):
    """Verify that ScannerExecutor enforces shell=False strictly on Popen."""
    mock_process = MagicMock()
    mock_process.communicate.return_value = ("", "")
    mock_process.returncode = 0
    mock_popen.return_value = mock_process
    
    executor = ScannerExecutor()
    executor.run_scanner(
        scanner_type=ScannerType.NMAP,
        cmd_args=["nmap", "127.0.0.1"],
        scan_id=uuid.uuid4()
    )
    
    # Verify Popen was called
    mock_popen.assert_called_once()
    
    # Extract kwargs
    kwargs = mock_popen.call_args[1]
    assert kwargs.get("shell") is False
