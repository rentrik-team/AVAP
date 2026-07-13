import logging
import threading

from app.core.enums import ScannerType
from app.core.exceptions import ParserException
from app.parsers.base_parser import BaseParser

logger = logging.getLogger(__name__)


class ParserRegistry:
    """Thread-safe registry for scanner parsers.

    Allows dynamic registration and lookup of parsers by ScannerType.
    """

    def __init__(self):
        self._parsers: dict[ScannerType, BaseParser] = {}
        self._lock = threading.Lock()

    def register(self, scanner_type: ScannerType, parser: BaseParser) -> None:
        """Register a parser for a given ScannerType.

        Args:
            scanner_type: The ScannerType key.
            parser: The BaseParser instance.
        """
        with self._lock:
            if scanner_type in self._parsers:
                logger.warning(
                    f"Overwriting existing scanner parser for {scanner_type.value}"
                )
            self._parsers[scanner_type] = parser
            logger.info(f"Registered scanner parser for {scanner_type.value}")

    def get_parser(self, scanner_type: ScannerType) -> BaseParser:
        """Retrieve the parser for a given ScannerType.

        Args:
            scanner_type: The ScannerType key.

        Returns:
            The registered BaseParser.

        Raises:
            ParserException if no parser is registered for that scanner type.
        """
        with self._lock:
            parser = self._parsers.get(scanner_type)
            if not parser:
                raise ParserException(
                    f"No parser registered for scanner type: {scanner_type.value}"
                )
            return parser

    def list_parsers(self) -> list[ScannerType]:
        """List all currently registered scanner types with parsers."""
        with self._lock:
            return list(self._parsers.keys())
