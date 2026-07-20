import pytest

from app.core.enums import ScannerType, ScanProfile
from app.core.exceptions import ValidationException
from app.scanners.execution_validator import ExecutionValidator


def test_execution_validator_valid_requests():
    validator = ExecutionValidator()

    # Valid IPv4
    validator.validate_request("192.168.1.1", ScannerType.NMAP, ScanProfile.DISCOVERY)
    validator.validate_request("192.168.1.1", ScannerType.OPENVAS, ScanProfile.FULL)

    # Valid Hostname
    validator.validate_request("example.com", ScannerType.NMAP, ScanProfile.PORT_SCAN)
    validator.validate_request("localhost", ScannerType.OPENVAS, ScanProfile.DISCOVERY)

    # Valid CIDR (Nmap only)
    validator.validate_request("10.0.0.0/24", ScannerType.NMAP, ScanProfile.DISCOVERY)


def test_execution_validator_invalid_targets():
    validator = ExecutionValidator()

    # Empty target
    with pytest.raises(ValidationException) as exc:
        validator.validate_request("", ScannerType.NMAP, ScanProfile.DISCOVERY)
    assert "Target value cannot be empty" in str(exc.value)

    # Invalid target formats
    invalid_targets = [
        "not-an-ip-or-host!",
        "300.400.500.600",
        "http://example.com",
        "1.2.3.4.5",
    ]
    for t in invalid_targets:
        with pytest.raises(ValidationException) as exc:
            validator.validate_request(t, ScannerType.NMAP, ScanProfile.DISCOVERY)
        assert "Invalid target format" in str(exc.value)


def test_execution_validator_unsupported_targets():
    validator = ExecutionValidator()

    # OpenVAS should reject CIDRs (based on validator config in execution_validator.py)
    with pytest.raises(ValidationException) as exc:
        validator.validate_request(
            "192.168.1.0/24", ScannerType.OPENVAS, ScanProfile.FULL
        )
    assert "does not support target type 'cidr'" in str(exc.value)


def test_execution_validator_shell_characters():
    validator = ExecutionValidator()

    # Even if hostname/IP format is syntactically passable (unlikely due
    # to regex, but test defense-in-depth) let's try injection attempts
    injection_targets = [
        "127.0.0.1; cat /etc/passwd",
        "127.0.0.1 && id",
        "example.com$(whoami)",
        "example.com`id`",
    ]
    for t in injection_targets:
        with pytest.raises(ValidationException):
            validator.validate_request(t, ScannerType.NMAP, ScanProfile.DISCOVERY)
