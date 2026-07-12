"""Application enumerations.

All enums use PascalCase names with UPPER_CASE members
per development standards.
"""

import enum


class TargetType(str, enum.Enum):
    """Classification of scan target types."""

    IPV4 = "IPV4"
    CIDR = "CIDR"
    HOSTNAME = "HOSTNAME"


class ScanStatus(str, enum.Enum):
    """Execution status of a scan job."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ScannerType(str, enum.Enum):
    """Supported scanner implementations."""

    NMAP = "NMAP"
    OPENVAS = "OPENVAS"


class ScanProfile(str, enum.Enum):
    """Predefined scan profiles controlling scanner behavior."""

    DISCOVERY = "DISCOVERY"
    PORT_SCAN = "PORT_SCAN"
    FULL = "FULL"


class ExecutionStatus(str, enum.Enum):
    """Outcome status of a scanner execution."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"


class RiskScope(str, enum.Enum):
    """Explicit scope of a persisted risk assessment record."""

    VULNERABILITY = "VULNERABILITY"
    ASSET = "ASSET"
    SCAN = "SCAN"
    ASSESSMENT = "ASSESSMENT"


class RiskLevel(str, enum.Enum):
    """Standardized deterministic risk categorization."""

    INFORMATIONAL = "INFORMATIONAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
