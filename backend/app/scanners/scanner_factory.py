import logging

from app.core.enums import ScannerType
from app.scanners.adapters.base_adapter import BaseScannerAdapter
from app.scanners.adapters.nmap_adapter import NmapAdapter
from app.scanners.adapters.openvas_adapter import OpenVASAdapter
from app.scanners.scanner_registry import ScannerRegistry

logger = logging.getLogger(__name__)


class ScannerFactory:
    """Factory for resolving scanner adapters from a registry.

    Initializes a default registry with Nmap and OpenVAS adapters,
    but allows passing a custom registry (useful for testing/mocking).
    """

    def __init__(self, registry: ScannerRegistry | None = None):
        if registry:
            self._registry = registry
        else:
            self._registry = ScannerRegistry()
            # Register default adapters
            self._registry.register(ScannerType.NMAP, NmapAdapter())
            self._registry.register(ScannerType.OPENVAS, OpenVASAdapter())

    def get_adapter(self, scanner_type: ScannerType) -> BaseScannerAdapter:
        """Resolve and return the appropriate scanner adapter.

        Args:
            scanner_type: The requested ScannerType.

        Returns:
            The corresponding BaseScannerAdapter implementation.
        """
        return self._registry.get_adapter(scanner_type)
