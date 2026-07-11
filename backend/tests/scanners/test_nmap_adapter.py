import pytest
from unittest.mock import MagicMock
import uuid
from pathlib import Path

from app.core.enums import ScannerType, ScanProfile
from app.core.exceptions import ScannerExecutionException
from app.scanners.adapters.nmap_adapter import NmapAdapter
from app.scanners.scan_artifact import ScanArtifact


def test_nmap_adapter_get_scanner_type():
    adapter = NmapAdapter()
    assert adapter.get_scanner_type() == ScannerType.NMAP


def test_nmap_adapter_build_command():
    adapter = NmapAdapter()

    # Discovery profile
    cmd = adapter.build_command("192.168.1.1", ScanProfile.DISCOVERY, "out.xml")
    assert "-sn" in cmd
    assert "-oX" in cmd
    assert "out.xml" in cmd
    assert cmd[-1] == "192.168.1.1"

    # Port Scan profile
    cmd = adapter.build_command("192.168.1.1", ScanProfile.PORT_SCAN, "out.xml")
    assert "-sT" in cmd
    assert "-F" in cmd
    assert "-oX" in cmd
    assert "out.xml" in cmd
    assert cmd[-1] == "192.168.1.1"

    # Full profile
    cmd = adapter.build_command("example.com", ScanProfile.FULL, "out.xml")
    assert "-sT" in cmd
    assert "-sV" in cmd
    assert "-oX" in cmd
    assert "out.xml" in cmd
    assert cmd[-1] == "example.com"


def test_nmap_adapter_build_command_sanitization():
    adapter = NmapAdapter()
    
    # Reject option injection in target
    with pytest.raises(ScannerExecutionException) as exc:
        adapter.build_command("-sS", ScanProfile.PORT_SCAN, "out.xml")
    assert "cannot start with a hyphen" in str(exc.value)


def test_nmap_adapter_execute():
    # Mock Executor
    mock_executor = MagicMock()
    mock_artifact = MagicMock(spec=ScanArtifact)
    mock_executor.run_scanner.return_value = mock_artifact

    adapter = NmapAdapter(executor=mock_executor)
    scan_id = uuid.uuid4()
    
    result = adapter.execute(scan_id, "192.168.1.1", ScanProfile.DISCOVERY)
    
    assert result is mock_artifact
    mock_executor.run_scanner.assert_called_once()
    
    # Assert output directory contains the XML filename
    call_args = mock_executor.run_scanner.call_args[1]
    assert call_args["scanner_type"] == ScannerType.NMAP
    assert call_args["scan_id"] == scan_id
    assert isinstance(call_args["output_path"], Path)
    assert call_args["output_path"].name == f"nmap_{scan_id}.xml"
