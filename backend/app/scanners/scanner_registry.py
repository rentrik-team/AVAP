import logging
import threading

from app.core.enums import ScannerType
from app.core.exceptions import ScannerExecutionException
from app.scanners.adapters.base_adapter import BaseScannerAdapter

logger = logging.getLogger(__name__)


class ScannerRegistry:
    """Thread-safe registry for scanner adapters.

    Allows dynamic registration and lookup of scanner adapters by ScannerType.
    """

    def __init__(self):
        self._adapters: dict[ScannerType, BaseScannerAdapter] = {}
        self._lock = threading.Lock()

    def register(self, scanner_type: ScannerType, adapter: BaseScannerAdapter) -> None:
        """Register an adapter for a given ScannerType.

        Args:
            scanner_type: The ScannerType key.
            adapter: The BaseScannerAdapter instance.
        """
        with self._lock:
            if scanner_type in self._adapters:
                logger.warning(
                    f"Overwriting existing scanner adapter for {scanner_type.value}"
                )
            self._adapters[scanner_type] = adapter
            logger.info(f"Registered scanner adapter for {scanner_type.value}")

    def get_adapter(self, scanner_type: ScannerType) -> BaseScannerAdapter:
        """Retrieve the adapter for a given ScannerType.

        Args:
            scanner_type: The ScannerType key.

        Returns:
            The registered BaseScannerAdapter.

        Raises:
            ScannerExecutionException if no adapter is registered for that scanner type.
        """
        with self._lock:
            adapter = self._adapters.get(scanner_type)
            if not adapter:
                raise ScannerExecutionException(
                    f"No adapter registered for scanner type: {scanner_type.value}"
                )
            return adapter

    def list_scanners(self) -> list[ScannerType]:
        """List all currently registered scanner types."""
        with self._lock:
            return list(self._adapters.keys())
