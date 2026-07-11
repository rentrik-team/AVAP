import pytest
from app.core.enums import ScannerType
from app.scanners.scanner_factory import ScannerFactory
from app.scanners.scanner_registry import ScannerRegistry
from app.scanners.adapters.nmap_adapter import NmapAdapter
from app.scanners.adapters.openvas_adapter import OpenVASAdapter


def test_scanner_factory_default_registry():
    """Verify factory initializes defaults (Nmap, OpenVAS)."""
    factory = ScannerFactory()
    
    nmap_adapter = factory.get_adapter(ScannerType.NMAP)
    assert isinstance(nmap_adapter, NmapAdapter)
    
    openvas_adapter = factory.get_adapter(ScannerType.OPENVAS)
    assert isinstance(openvas_adapter, OpenVASAdapter)


def test_scanner_factory_custom_registry():
    """Verify factory accepts and uses a custom registry."""
    registry = ScannerRegistry()
    mock_adapter = NmapAdapter()
    registry.register(ScannerType.NMAP, mock_adapter)

    factory = ScannerFactory(registry=registry)
    assert factory.get_adapter(ScannerType.NMAP) is mock_adapter
