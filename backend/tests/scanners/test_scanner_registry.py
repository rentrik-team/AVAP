import pytest

from app.core.enums import ScannerType
from app.core.exceptions import ScannerExecutionException
from app.scanners.adapters.base_adapter import BaseScannerAdapter
from app.scanners.scanner_registry import ScannerRegistry


class MockAdapter(BaseScannerAdapter):
    def get_scanner_type(self) -> ScannerType:
        return ScannerType.NMAP

    def build_command(self, target, scan_profile, output_path):
        return ["mock", target]

    def execute(self, scan_id, target, scan_profile):
        pass


def test_scanner_registry_operations():
    registry = ScannerRegistry()
    adapter = MockAdapter()

    # Get non-existent
    with pytest.raises(ScannerExecutionException) as excinfo:
        registry.get_adapter(ScannerType.NMAP)
    assert "No adapter registered" in str(excinfo.value)

    # Register and get
    registry.register(ScannerType.NMAP, adapter)
    assert registry.get_adapter(ScannerType.NMAP) is adapter
    assert registry.list_scanners() == [ScannerType.NMAP]
