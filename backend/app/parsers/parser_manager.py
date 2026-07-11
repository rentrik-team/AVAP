import logging
from typing import Optional

from app.core.exceptions import ParserException
from app.parsers.models import AssessmentPackage
from app.parsers.parser_factory import ParserFactory
from app.scanners.scan_artifact import ScanArtifact

logger = logging.getLogger(__name__)


class ParserManager:
    """Entry point and coordinator for the Parser Engine.
    
    Validates scan artifacts, selects parsers, and returns unified AssessmentPackages.
    """

    def __init__(self, factory: Optional[ParserFactory] = None):
        self.factory = factory or ParserFactory()

    def parse_artifact(self, artifact: ScanArtifact) -> AssessmentPackage:
        """Parse scan artifact and return unified platform AssessmentPackage.
        
        Args:
            artifact: The ScanArtifact representing scanner run results.
            
        Returns:
            The normalized, validated AssessmentPackage.
            
        Raises:
            ParserException if parsing fails, file is missing, or status is invalid.
        """
        logger.info(
            "Request to parse scan artifact",
            extra={
                "scan_id": str(artifact.scan_id),
                "artifact_id": str(artifact.artifact_id),
                "scanner_type": artifact.scanner_type.value,
                "status": artifact.execution_status.value
            }
        )

        # 1. Check artifact status
        if not artifact.is_successful:
            raise ParserException(
                f"Cannot parse unsuccessful scan artifact. Execution status: {artifact.execution_status.value}"
            )

        # 2. Check output file existence
        if not artifact.output_path:
            raise ParserException("Scan artifact does not specify an output path.")

        if not artifact.has_output:
            raise ParserException(
                f"Scan artifact output file does not exist: {artifact.output_path}"
            )

        # 3. Resolve parser via factory
        parser = self.factory.get_parser(artifact.scanner_type)

        # 4. Parse artifact
        try:
            package = parser.parse(artifact)
        except ParserException:
            raise
        except Exception as e:
            logger.exception(
                "Unexpected failure in parser engine execution",
                extra={"scan_id": str(artifact.scan_id), "scanner": artifact.scanner_type.value}
            )
            raise ParserException(f"Parser engine internal error: {e}") from e

        logger.info(
            "Parser manager completed parsing artifact successfully",
            extra={
                "scan_id": str(artifact.scan_id),
                "artifact_id": str(artifact.artifact_id),
                "hosts_found": len(package.parsed_hosts)
            }
        )

        return package
