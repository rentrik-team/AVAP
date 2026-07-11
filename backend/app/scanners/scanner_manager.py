import logging
import uuid
from typing import Optional

from app.core.enums import ScannerType, ScanProfile
from app.core.exceptions import ValidationException
from app.scanners.interfaces import IScannerEngine
from app.scanners.scan_artifact import ScanArtifact
from app.scanners.scanner_factory import ScannerFactory
from app.scanners.execution_validator import ExecutionValidator

logger = logging.getLogger(__name__)


class ScannerManager(IScannerEngine):
    """Entry point for all scanner execution requests.
    
    Orchestrates validation, adapter lookup, execution, and artifact retrieval.
    """

    def __init__(
        self,
        factory: Optional[ScannerFactory] = None,
        validator: Optional[ExecutionValidator] = None
    ):
        self.factory = factory or ScannerFactory()
        self.validator = validator or ExecutionValidator()

    def _parse_scan_profile(self, scan_profile: str) -> ScanProfile:
        """Map string profile identifier to ScanProfile enum.
        
        Args:
            scan_profile: The string profile name (case-insensitive).
            
        Returns:
            The ScanProfile enum.
            
        Raises:
            ValidationException if the profile name is invalid.
        """
        norm_profile = scan_profile.strip().upper()
        
        # Also map common alternate spellings/cases if needed
        # e.g., 'PING' -> 'DISCOVERY'
        if norm_profile in ["DISCOVERY", "PING", "PING_SCAN"]:
            return ScanProfile.DISCOVERY
        elif norm_profile in ["PORT_SCAN", "PORT", "PORTS", "FAST"]:
            return ScanProfile.PORT_SCAN
        elif norm_profile in ["FULL", "DEEP", "ALL"]:
            return ScanProfile.FULL
            
        try:
            return ScanProfile[norm_profile]
        except KeyError:
            raise ValidationException(
                f"Invalid scan profile: '{scan_profile}'. "
                f"Supported profiles: {[p.name for p in ScanProfile]}"
            )

    def dispatch_scan(
        self, 
        scan_id: uuid.UUID, 
        target: str, 
        scan_profile: str,
        scanner_type: Optional[ScannerType] = None
    ) -> ScanArtifact:
        """Validate and execute a scan against a target.
        
        Args:
            scan_id: The unique identifier of the scan job.
            target: The target IP, CIDR, or hostname.
            scan_profile: The scan profile (string).
            scanner_type: Optional scanner type (defaults to NMAP).
            
        Returns:
            A ScanArtifact containing the results of the execution.
        """
        # Resolve scanner type default
        resolved_scanner = scanner_type or ScannerType.NMAP
        
        # Parse profile
        resolved_profile = self._parse_scan_profile(scan_profile)

        logger.info(
            "Dispatching scan request",
            extra={
                "scan_id": str(scan_id),
                "target": target,
                "scanner_type": resolved_scanner.value,
                "profile": resolved_profile.value
            }
        )

        # Validate request (target format, security constraints, compatibility)
        self.validator.validate_request(target, resolved_scanner, resolved_profile)

        # Resolve adapter via factory
        adapter = self.factory.get_adapter(resolved_scanner)

        # Execute scan via adapter
        artifact = adapter.execute(scan_id, target, resolved_profile)
        
        logger.info(
            "Scan dispatch completed",
            extra={
                "scan_id": str(scan_id),
                "status": artifact.execution_status.value,
                "duration": artifact.execution_duration_seconds
            }
        )
        
        return artifact
