import logging

from app.core.enums import ScannerType
from app.parsers.base_parser import BaseParser
from app.parsers.nmap_parser import NmapParser

# OpenVAS is disabled for now — see the matching comment in
# app/scanners/scanner_factory.py. The parser itself is real and correct
# (it would work against genuine OpenVAS report XML), but with no adapter
# producing that XML there's nothing for it to ever receive in practice.
# from app.parsers.openvas_parser import OpenVASParser
from app.parsers.parser_registry import ParserRegistry

logger = logging.getLogger(__name__)


class ParserFactory:
    """Factory for resolving scanner parsers from a registry.

    Initializes a default registry with the Nmap parser (OpenVAS is
    currently disabled — see the import comment above), but allows passing
    a custom registry (useful for testing/mocking).
    """

    def __init__(self, registry: ParserRegistry | None = None):
        if registry:
            self._registry = registry
        else:
            self._registry = ParserRegistry()
            # Register default parsers
            self._registry.register(ScannerType.NMAP, NmapParser())
            # self._registry.register(ScannerType.OPENVAS, OpenVASParser())

    def get_parser(self, scanner_type: ScannerType) -> BaseParser:
        """Resolve and return the appropriate scanner parser.

        Args:
            scanner_type: The requested ScannerType.

        Returns:
            The corresponding BaseParser implementation.
        """
        return self._registry.get_parser(scanner_type)
