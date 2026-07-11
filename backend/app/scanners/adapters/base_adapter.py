from abc import ABC, abstractmethod
import uuid
from typing import List

from app.core.enums import ScannerType, ScanProfile
from app.scanners.scan_artifact import ScanArtifact


class BaseScannerAdapter(ABC):
    """Abstract Base Class defining the contract for all scanner adapters.
    
    Each supported security scanner (e.g., Nmap, OpenVAS) must implement
    this interface.
    """

    @abstractmethod
    def get_scanner_type(self) -> ScannerType:
        """Return the scanner type this adapter handles."""
        pass

    @abstractmethod
    def build_command(self, target: str, scan_profile: ScanProfile, output_path: str) -> List[str]:
        """Construct the secure command-line argument list for the scanner.
        
        Args:
            target: The normalized target IP/hostname/CIDR.
            scan_profile: The ScanProfile enum value.
            output_path: The file path where the scanner should write its output.
            
        Returns:
            A list of command-line arguments starting with the executable.
        """
        pass

    @abstractmethod
    def execute(self, scan_id: uuid.UUID, target: str, scan_profile: ScanProfile) -> ScanArtifact:
        """Execute the scan and return a standardized ScanArtifact.
        
        Args:
            scan_id: The unique scan job identifier.
            target: The normalized target IP/hostname/CIDR.
            scan_profile: The ScanProfile enum value.
            
        Returns:
            A standardized ScanArtifact containing execution details and results.
        """
        pass
