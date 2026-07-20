import logging

from app.core.enums import ScannerType, ScanProfile
from app.core.exceptions import ValidationException
from app.core.security import is_valid_hostname, is_valid_ipv4, is_valid_ipv4_cidr

logger = logging.getLogger(__name__)


class ExecutionValidator:
    """Validates scan execution requests before they reach the execution phase.

    Acts as a security and capability guard.
    """

    def __init__(self):
        # Define supported target types per scanner type
        self._supported_targets = {
            ScannerType.NMAP: {"ipv4", "cidr", "hostname"},
            ScannerType.OPENVAS: {
                "ipv4",
                "hostname",
            },  # CIDR usually requires task splitting or distinct handling
        }

    def validate_request(
        self, target: str, scanner_type: ScannerType, scan_profile: ScanProfile
    ) -> None:
        """Validate target format, scanner type, and target-scanner compatibility.

        Args:
            target: The raw/normalized target string.
            scanner_type: The requested ScannerType enum.
            scan_profile: The requested ScanProfile enum.

        Raises:
            ValidationException if validation fails.
        """
        if not target:
            raise ValidationException("Target value cannot be empty.")

        # Determine target type
        target_type = None
        if is_valid_ipv4(target):
            target_type = "ipv4"
        elif is_valid_ipv4_cidr(target):
            target_type = "cidr"
        elif is_valid_hostname(target):
            target_type = "hostname"

        if not target_type:
            raise ValidationException(
                f"Invalid target format: '{target}' is not a valid IPv4 "
                "address, CIDR range, or hostname."
            )

        # Check scanner support for the target type
        allowed_types = self._supported_targets.get(scanner_type, set())
        if target_type not in allowed_types:
            raise ValidationException(
                f"Scanner {scanner_type.value} does not support target "
                f"type '{target_type}' ('{target}')."
            )

        # Additional defense-in-depth sanitization check
        # Even though we use shell=False, we explicitly reject targets
        # containing common shell metacharacters
        shell_chars = [";", "&&", "||", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
        if any(char in target for char in shell_chars):
            raise ValidationException(
                "Target value contains disallowed shell characters."
            )

        logger.debug(
            "Scan request validation passed",
            extra={
                "target": target,
                "scanner_type": scanner_type.value,
                "target_type": target_type,
            },
        )
