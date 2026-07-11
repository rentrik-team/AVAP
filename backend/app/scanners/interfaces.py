from typing import Protocol
import uuid


class IScannerEngine(Protocol):
    """
    Interface for the Scanner Engine.
    
    This interface abstracts the scanner execution logic from the Scan Management module,
    allowing the Scan Management module to remain decoupled from the actual implementation 
    (Nmap, OpenVAS, etc.), which will be developed in Module 03.
    """

    def dispatch_scan(self, scan_id: uuid.UUID, target: str, scan_profile: str) -> None:
        """
        Dispatch a scan job to the scanner engine.
        
        Args:
            scan_id: The unique identifier of the scan job.
            target: The normalized target string (e.g., IP address or hostname).
            scan_profile: The type of scan to perform.
        """
        ...
