import logging
from typing import Optional

from app.core.enums import ScannerType
from app.parsers.nmap_parser import NmapParser
from app.parsers.openvas_parser import OpenVASParser
from app.parsers.parser_registry import ParserRegistry
from app.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """Factory for resolving scanner parsers from a registry.
    
    Initializes a default registry with Nmap and OpenVAS parsers, 
    but allows passing a custom registry (useful for testing/mocking).
    """

    def __init__(self, registry: Optional[ParserRegistry] = None):
        if registry:
            self._registry = registry
        else:
            self._registry = ParserRegistry()
            # Register default parsers
            self._registry.register(ScannerType.NMAP, NmapParser())
            self._registry.register(ScannerType.OPENVAS, OpenVASParser())

    def get_parser(self, scanner_type: ScannerType) -> BaseParser:
        """Resolve and return the appropriate scanner parser.
        
        Args:
            scanner_type: The requested ScannerType.
            
        Returns:
            The corresponding BaseParser implementation.
        """
        return self._registry.get_parser(scanner_type)
