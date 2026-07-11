import pytest
from unittest.mock import MagicMock
import uuid

from app.core.enums import ScannerType, ScanProfile
from app.core.exceptions import ValidationException
from app.scanners.scanner_manager import ScannerManager
from app.scanners.scan_artifact import ScanArtifact


def test_scanner_manager_profile_parsing():
    manager = ScannerManager()

    # Success cases
    assert manager._parse_scan_profile("discovery") == ScanProfile.DISCOVERY
    assert manager._parse_scan_profile("ping") == ScanProfile.DISCOVERY
    assert manager._parse_scan_profile("port_scan") == ScanProfile.PORT_SCAN
    assert manager._parse_scan_profile("FAST") == ScanProfile.PORT_SCAN
    assert manager._parse_scan_profile("full") == ScanProfile.FULL

    # Invalid profile
    with pytest.raises(ValidationException) as exc:
        manager._parse_scan_profile("ultra_deep_unsupported_scan")
    assert "Invalid scan profile" in str(exc.value)


def test_scanner_manager_dispatch_scan():
    # Mock Validator, Factory, Adapter, and Artifact
    mock_validator = MagicMock()
    mock_factory = MagicMock()
    mock_adapter = MagicMock()
    mock_artifact = MagicMock(spec=ScanArtifact)

    mock_factory.get_adapter.return_value = mock_adapter
    mock_adapter.execute.return_value = mock_artifact

    manager = ScannerManager(factory=mock_factory, validator=mock_validator)
    
    scan_id = uuid.uuid4()
    target = "192.168.1.1"

    # Default scanner type is NMAP
    result = manager.dispatch_scan(scan_id, target, "discovery")

    assert result is mock_artifact
    mock_validator.validate_request.assert_called_once_with(
        target, ScannerType.NMAP, ScanProfile.DISCOVERY
    )
    mock_factory.get_adapter.assert_called_once_with(ScannerType.NMAP)
    mock_adapter.execute.assert_called_once_with(
        scan_id, target, ScanProfile.DISCOVERY
    )
