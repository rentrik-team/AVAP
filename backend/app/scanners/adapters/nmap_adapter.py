import logging
import os
import uuid
from pathlib import Path
from typing import List, Optional

from app.core.config import get_settings
from app.core.enums import ScannerType, ScanProfile
from app.core.exceptions import ScannerExecutionException
from app.scanners.adapters.base_adapter import BaseScannerAdapter
from app.scanners.scan_artifact import ScanArtifact
from app.scanners.scanner_executor import ScannerExecutor

logger = logging.getLogger(__name__)


class NmapAdapter(BaseScannerAdapter):
    """Adapter for Nmap port scanner.
    
    Translates high-level targets and profiles into secure Nmap command arguments
    and manages the execution via ScannerExecutor.
    """

    def __init__(self, executor: Optional[ScannerExecutor] = None):
        self.settings = get_settings()
        self.executor = executor or ScannerExecutor()

    def get_scanner_type(self) -> ScannerType:
        return ScannerType.NMAP

    def _sanitize_target(self, target: str) -> str:
        """Sanitize target to prevent command-line option injection.
        
        Args:
            target: The raw target string.
            
        Returns:
            The sanitized target.
        """
        sanitized = target.strip()
        # Prevent target from starting with a hyphen, which could be interpreted as an option
        if sanitized.startswith("-"):
            raise ScannerExecutionException(
                f"Invalid scan target: '{target}' cannot start with a hyphen."
            )
        return sanitized

    def build_command(self, target: str, scan_profile: ScanProfile, output_path: str) -> List[str]:
        """Construct the secure command-line argument list for Nmap.
        
        Args:
            target: The normalized target IP/hostname/CIDR.
            scan_profile: The ScanProfile enum value.
            output_path: The file path where the scanner should write its XML output.
            
        Returns:
            A list of command-line arguments starting with the Nmap executable.
        """
        sanitized_target = self._sanitize_target(target)
        executable = self.settings.nmap_executable

        # Default fallback if setting is empty
        if not executable:
            executable = "nmap"

        # XML output flag is mandatory for parser to consume
        args = [executable]

        # Configure scan options based on profile
        if scan_profile == ScanProfile.DISCOVERY:
            args.extend(["-sn"])  # Ping scan (no port scan)
        elif scan_profile == ScanProfile.PORT_SCAN:
            args.extend(["-sT", "-F"])  # TCP Connect scan, Fast mode
        elif scan_profile == ScanProfile.FULL:
            args.extend(["-sT", "-sV"])  # TCP Connect scan + Service Version detection
        else:
            # Fallback/default if unrecognized
            args.extend(["-sT"])

        # Output to XML file
        args.extend(["-oX", output_path])
        
        # Append target at the very end
        args.append(sanitized_target)

        return args

    def execute(self, scan_id: uuid.UUID, target: str, scan_profile: ScanProfile) -> ScanArtifact:
        """Execute the Nmap scan and return a standardized ScanArtifact.
        
        Args:
            scan_id: The unique scan job identifier.
            target: The normalized target IP/hostname/CIDR.
            scan_profile: The ScanProfile enum value.
            
        Returns:
            A standardized ScanArtifact containing execution details and results.
        """
        # Ensure output directory exists
        output_dir = self.settings.scanner_output_path
        output_dir.mkdir(parents=True, exist_ok=True)

        # Build unique output file path
        filename = f"nmap_{scan_id}.xml"
        output_path = output_dir / filename

        cmd_args = self.build_command(target, scan_profile, str(output_path))

        try:
            artifact = self.executor.run_scanner(
                scanner_type=ScannerType.NMAP,
                cmd_args=cmd_args,
                scan_id=scan_id,
                output_path=output_path
            )
            return artifact
        except Exception as e:
            logger.error(
                f"Failed to execute Nmap scan: {e}",
                extra={"scan_id": str(scan_id), "target": target}
            )
            raise
