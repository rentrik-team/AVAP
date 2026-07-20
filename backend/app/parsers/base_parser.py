from abc import ABC, abstractmethod

from app.parsers.models import AssessmentPackage
from app.scanners.scan_artifact import ScanArtifact


class BaseParser(ABC):
    """Abstract Base Class defining the parsing contract for all scan parsers.

    Each scanner-specific parser must implement this class to map raw outputs
    into the scanner-independent AssessmentPackage.
    """

    @abstractmethod
    def parse(self, artifact: ScanArtifact) -> AssessmentPackage:
        """Parse raw scanner output file from artifact into an AssessmentPackage.

        Args:
            artifact: The ScanArtifact produced by the Scanner Engine.

        Returns:
            A unified AssessmentPackage containing normalized hosts,
            services, and vulnerabilities.

        Raises:
            ParserException if parsing, validation, or schema loading fails.
        """
        pass
