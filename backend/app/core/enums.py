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
    CANCELLED = "CANCELLED"


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
    CANCELLED = "CANCELLED"


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


class AuditEventCategory(str, enum.Enum):
    """High-level domain grouping for an audit event, independent of the
    specific event_type. Enables coarse filtering without enumerating every
    event type. SYSTEM is reserved for future platform lifecycle events
    (startup/shutdown) and is not currently emitted by any integration.
    """

    SYSTEM = "SYSTEM"
    TARGET = "TARGET"
    SCAN = "SCAN"
    INVENTORY = "INVENTORY"
    RISK = "RISK"
    AI = "AI"
    REPORT = "REPORT"


class AuditEventType(str, enum.Enum):
    """Centralized, stable audit event taxonomy.

    Every persisted AuditEvent uses exactly one of these values. Event names
    are deliberately specific (resource + action) rather than generic, so
    they remain meaningful for future SOC review, SIEM forwarding, and
    filtering without re-deriving meaning from free-text descriptions.
    """

    TARGET_CREATED = "TARGET_CREATED"
    TARGET_UPDATED = "TARGET_UPDATED"
    TARGET_DELETED = "TARGET_DELETED"

    SCAN_CREATED = "SCAN_CREATED"
    SCAN_DELETED = "SCAN_DELETED"
    SCAN_COMPLETED = "SCAN_COMPLETED"
    SCAN_FAILED = "SCAN_FAILED"
    SCAN_CANCELLED = "SCAN_CANCELLED"

    AI_VULNERABILITY_DISCOVERY_COMPLETED = "AI_VULNERABILITY_DISCOVERY_COMPLETED"
    AI_VULNERABILITY_DISCOVERY_FAILED = "AI_VULNERABILITY_DISCOVERY_FAILED"

    INVENTORY_PROCESSED = "INVENTORY_PROCESSED"
    INVENTORY_PROCESSING_FAILED = "INVENTORY_PROCESSING_FAILED"

    RISK_CALCULATION_COMPLETED = "RISK_CALCULATION_COMPLETED"
    RISK_CALCULATION_FAILED = "RISK_CALCULATION_FAILED"

    AI_RECOMMENDATION_GENERATED = "AI_RECOMMENDATION_GENERATED"
    AI_RECOMMENDATION_FAILED = "AI_RECOMMENDATION_FAILED"

    REPORT_GENERATED = "REPORT_GENERATED"
    REPORT_GENERATION_FAILED = "REPORT_GENERATION_FAILED"
    REPORT_DOWNLOADED = "REPORT_DOWNLOADED"
    REPORT_DELETED = "REPORT_DELETED"


class AuditOutcome(str, enum.Enum):
    """Structured outcome of an audited business action.

    Only SUCCESS/FAILURE are used by the current integrations; no audited
    operation in this implementation has DENIED/PARTIAL/CANCELLED semantics.
    """

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class AuditActorType(str, enum.Enum):
    """Actor classification for an audit event.

    AVAP currently has no authentication, users, or RBAC. SYSTEM represents
    an action performed by internal orchestration with no HTTP caller (e.g.
    a service invoked directly rather than through a route). ANONYMOUS
    represents any current HTTP-triggered action, since no caller identity
    can be established yet. An AUTHENTICATED_USER value is deliberately not
    defined until real authentication exists — adding it later is a
    backward-compatible enum extension, not a redesign.
    """

    SYSTEM = "SYSTEM"
    ANONYMOUS = "ANONYMOUS"


class AuditResourceType(str, enum.Enum):
    """The kind of resource an audit event's resource_id refers to.

    Stored without a foreign key: audit evidence must survive deletion of
    the referenced business resource.
    """

    TARGET = "TARGET"
    SCAN = "SCAN"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    AI_RECOMMENDATION = "AI_RECOMMENDATION"
    REPORT = "REPORT"
