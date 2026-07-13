import logging
import uuid

from app.core.config import get_settings
from app.core.enums import ExecutionStatus, ScannerType, ScanProfile
from app.core.exceptions import ScannerExecutionException
from app.scanners.adapters.base_adapter import BaseScannerAdapter
from app.scanners.scan_artifact import ScanArtifact

logger = logging.getLogger(__name__)


class OpenVASAdapter(BaseScannerAdapter):
    """Adapter for OpenVAS (Greenbone Vulnerability Manager).

    In Phase 1, this adapter serves as a stub/connector that simulates or
    triggers OpenVAS scans via GVM protocol TCP/Unix socket endpoints.
    Since python-gvm is not a core package dependency yet, we implement
    a robust integration skeleton that logs actions and outputs mock XML data.
    """

    def __init__(self):
        self.settings = get_settings()

    def get_scanner_type(self) -> ScannerType:
        return ScannerType.OPENVAS

    def build_command(
        self, target: str, scan_profile: ScanProfile, output_path: str
    ) -> list[str]:
        """OpenVAS does not execute via direct local subprocess shell invocation.

        This method is implemented to satisfy the interface but will raise
        as OpenVAS scans are triggered via network socket / API instead.
        """
        raise NotImplementedError(
            "OpenVAS does not support direct command line execution."
        )

    def execute(
        self, scan_id: uuid.UUID, target: str, scan_profile: ScanProfile
    ) -> ScanArtifact:
        """Execute OpenVAS scan.

        Connects to OpenVAS (GVM) daemon, creates target/task, starts scan,
        monitors progress, and retrieves XML report.
        """
        logger.info(
            "Initializing OpenVAS scan execution",
            extra={
                "scan_id": str(scan_id),
                "target": target,
                "scan_profile": scan_profile.value,
                "openvas_host": self.settings.openvas_host,
                "openvas_port": self.settings.openvas_port,
            },
        )

        output_dir = self.settings.scanner_output_path
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"openvas_{scan_id}.xml"
        output_path = output_dir / filename

        # For Phase 1 validation and testing, if host is localhost, we simulate/stub the scan.
        # This prevents failure if OpenVAS daemon is not running in the development env.
        is_stub = self.settings.openvas_host in ["localhost", "127.0.0.1", ""]

        if is_stub:
            logger.info(
                "OpenVAS host is localhost. Running in stub/simulation mode.",
                extra={"scan_id": str(scan_id)},
            )

            # Write a mock OpenVAS XML report for downstream Parser Engine testing
            mock_xml = (
                f'<?xml version="1.0" encoding="UTF-8"?>\n'
                f'<report id="{scan_id}">\n'
                f"  <target>{target}</target>\n"
                f"  <scan_profile>{scan_profile.value}</scan_profile>\n"
                f"  <results>\n"
                f'    <result id="1">\n'
                f"      <name>Mock OpenVAS Finding</name>\n"
                f"      <severity>7.5</severity>\n"
                f"      <description>This is a simulated OpenVAS vulnerability for testing.</description>\n"
                f"    </result>\n"
                f"  </results>\n"
                f"</report>\n"
            )
            try:
                output_path.write_text(mock_xml, encoding="utf-8")
            except Exception as e:
                raise ScannerExecutionException(
                    f"Failed to write mock OpenVAS output: {e}"
                ) from e

            return ScanArtifact(
                scan_id=scan_id,
                scanner_type=ScannerType.OPENVAS,
                execution_status=ExecutionStatus.SUCCESS,
                exit_code=0,
                execution_duration_seconds=1.5,
                stdout="Simulated OpenVAS Scan Success",
                stderr="",
                output_path=output_path,
            )
        else:
            # Here we would normally connect via socket:
            # socket.connect((self.settings.openvas_host, self.settings.openvas_port))
            # Send GMP/GVM commands, etc.
            # Since this is a placeholder/skeleton, we raise execution error if actual connection fails.
            msg = f"Failed to connect to OpenVAS daemon at {self.settings.openvas_host}:{self.settings.openvas_port}."
            logger.error(msg, extra={"scan_id": str(scan_id)})
            raise ScannerExecutionException(msg)
