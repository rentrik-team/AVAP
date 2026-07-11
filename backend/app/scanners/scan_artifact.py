"""Standardized scanner output representation.

Every scanner execution produces a ScanArtifact, regardless of success or failure.
Downstream consumers (Parser Engine) receive ScanArtifacts rather than
scanner-specific raw output formats.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from app.core.enums import ExecutionStatus, ScannerType


@dataclass(frozen=True)
class ScanArtifact:
    """Immutable representation of a scanner execution result.

    Attributes:
        artifact_id: Unique identifier for this artifact.
        scan_id: The scan job ID that triggered this execution.
        scanner_type: Which scanner produced this artifact.
        execution_status: Outcome of the execution.
        exit_code: Process exit code (None if process did not start).
        execution_duration_seconds: Wall-clock time for the execution.
        stdout: Captured standard output from the scanner process.
        stderr: Captured standard error from the scanner process.
        output_path: Path to the scanner's output file on disk (e.g., Nmap XML).
        created_at: Timestamp when the artifact was created.
        metadata: Additional scanner-specific metadata.
    """

    artifact_id: uuid.UUID = field(default_factory=uuid.uuid4)
    scan_id: uuid.UUID = field(default_factory=uuid.uuid4)
    scanner_type: ScannerType = ScannerType.NMAP
    execution_status: ExecutionStatus = ExecutionStatus.ERROR
    exit_code: Optional[int] = None
    execution_duration_seconds: float = 0.0
    stdout: str = ""
    stderr: str = ""
    output_path: Optional[Path] = None
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_successful(self) -> bool:
        """Whether the scanner execution completed successfully."""
        return self.execution_status == ExecutionStatus.SUCCESS

    @property
    def has_output(self) -> bool:
        """Whether the artifact has a valid output file."""
        return self.output_path is not None and self.output_path.exists()
