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
