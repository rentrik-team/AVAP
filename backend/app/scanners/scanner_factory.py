import logging

from app.core.enums import ScannerType
from app.scanners.adapters.base_adapter import BaseScannerAdapter
from app.scanners.adapters.nmap_adapter import NmapAdapter

# OpenVAS is disabled for now: no OpenVAS/GVM server is available in this
# environment, and OpenVASAdapter is a stub with no real client (see its
# own docstring) — registering it would let a scan silently "succeed"
# against fabricated mock data. Re-enable by uncommenting the import and
# the registry.register(...) call below once a real GVM client exists and
# an OpenVAS server is reachable.
# from app.scanners.adapters.openvas_adapter import OpenVASAdapter
from app.scanners.scanner_registry import ScannerRegistry

logger = logging.getLogger(__name__)


class ScannerFactory:
    """Factory for resolving scanner adapters from a registry.

    Initializes a default registry with the Nmap adapter (OpenVAS is
    currently disabled — see the import comment above), but allows passing
    a custom registry (useful for testing/mocking).
    """

    def __init__(self, registry: ScannerRegistry | None = None):
        if registry:
            self._registry = registry
        else:
            self._registry = ScannerRegistry()
            # Register default adapters
            self._registry.register(ScannerType.NMAP, NmapAdapter())
            # self._registry.register(ScannerType.OPENVAS, OpenVASAdapter())

    def get_adapter(self, scanner_type: ScannerType) -> BaseScannerAdapter:
        """Resolve and return the appropriate scanner adapter.

        Args:
            scanner_type: The requested ScannerType.

        Returns:
            The corresponding BaseScannerAdapter implementation.
        """
        return self._registry.get_adapter(scanner_type)
