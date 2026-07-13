import uuid
from typing import Protocol

from app.core.enums import ScannerType
from app.scanners.scan_artifact import ScanArtifact


class IScannerEngine(Protocol):
    """
    Interface for the Scanner Engine.

    This interface abstracts the scanner execution logic from the Scan Management module,
    allowing the Scan Management module to remain decoupled from the actual implementation
    (Nmap, OpenVAS, etc.).
    """

    def dispatch_scan(
        self,
        scan_id: uuid.UUID,
        target: str,
        scan_profile: str,
        scanner_type: ScannerType | None = None,
    ) -> ScanArtifact:
        """
        Dispatch a scan job to the scanner engine.

        Args:
            scan_id: The unique identifier of the scan job.
            target: The normalized target string (e.g., IP address or hostname).
            scan_profile: The type of scan/profile to perform.
            scanner_type: Optional scanner type (defaults to NMAP if not specified).

        Returns:
            A ScanArtifact containing the results of the execution.
        """
        ...
