import logging
import os
import subprocess  # nosec B404 -- shell=False, whitelisted argv only, see call site below
import time
import uuid
from pathlib import Path

from app.core.config import get_settings
from app.core.enums import ExecutionStatus, ScannerType
from app.core.exceptions import ScannerExecutionException, ScannerTimeoutException
from app.scanners.scan_artifact import ScanArtifact

logger = logging.getLogger(__name__)


class ScannerExecutor:
    """Securely executes scanner subprocesses.

    Handles timeout management, exit code validation, output capturing,
    and sanitization to prevent command injection.
    """

    def __init__(self):
        self.settings = get_settings()
        # Whitelist of allowed executables
        self._executable_whitelist = {
            ScannerType.NMAP: ["nmap", "nmap.exe"],
            # OpenVAS is currently stubbed/handled via API, but if CLI is used, whitelist here.
        }

    def _validate_executable(
        self, scanner_type: ScannerType, cmd_args: list[str]
    ) -> str:
        """Validate that the executable is in the whitelist for the given scanner type.

        Args:
            scanner_type: The scanner type (e.g., ScannerType.NMAP).
            cmd_args: The command arguments list.

        Returns:
            The validated executable path/name.
        """
        if not cmd_args:
            raise ScannerExecutionException("Empty command arguments list.")

        executable = cmd_args[0]
        # Resolve the basename of the executable (e.g. "/usr/bin/nmap" -> "nmap")
        basename = os.path.basename(executable).lower()

        allowed = self._executable_whitelist.get(scanner_type, [])
        if basename not in allowed and executable not in allowed:
            # Let's check if the configured setting matches the executable
            configured_exec = ""
            if scanner_type == ScannerType.NMAP:
                configured_exec = self.settings.nmap_executable

            if configured_exec and (
                executable == configured_exec
                or os.path.basename(configured_exec).lower() == basename
            ):
                return executable

            raise ScannerExecutionException(
                f"Unauthorized executable: '{executable}' is not allowed for scanner type {scanner_type.value}."
            )

        return executable

    def run_scanner(
        self,
        scanner_type: ScannerType,
        cmd_args: list[str],
        scan_id: uuid.UUID,
        output_path: Path | None = None,
        timeout: int | None = None,
    ) -> ScanArtifact:
        """Securely execute a scanner command as a subprocess.

        Args:
            scanner_type: The type of scanner being run.
            cmd_args: The list of command arguments (first item must be the executable).
            scan_id: The ID of the scan job triggering this execution.
            output_path: Optional path to the output file written by the scanner.
            timeout: Optional execution timeout in seconds.

        Returns:
            A ScanArtifact containing the results of the execution.
        """
        self._validate_executable(scanner_type, cmd_args)

        if timeout is None:
            timeout = self.settings.scan_timeout

        logger.info(
            "Executing scanner process",
            extra={
                "scan_id": str(scan_id),
                "scanner_type": scanner_type.value,
                "command": " ".join(cmd_args),
                "timeout": timeout,
            },
        )

        start_time = time.time()
        stdout_data = ""
        stderr_data = ""
        exit_code = None
        status = ExecutionStatus.ERROR

        try:
            # shell=False is mandatory to prevent command injection. cmd_args
            # is not raw user input: the executable was whitelist-validated
            # above, and callers build cmd_args from validated scan targets
            # (app/scanners/execution_validator.py) plus fixed scanner flags.
            process = subprocess.Popen(  # noqa: S603 # nosec B603
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
            )

            try:
                stdout_data, stderr_data = process.communicate(timeout=timeout)
                exit_code = process.returncode
                if exit_code == 0:
                    status = ExecutionStatus.SUCCESS
                else:
                    status = ExecutionStatus.FAILED
                    logger.warning(
                        "Scanner process returned non-zero exit code",
                        extra={
                            "scan_id": str(scan_id),
                            "exit_code": exit_code,
                            "stderr": stderr_data,
                        },
                    )
            except subprocess.TimeoutExpired as exc:
                process.kill()
                stdout_data, stderr_data = process.communicate()
                exit_code = process.returncode
                status = ExecutionStatus.TIMEOUT
                logger.error(
                    "Scanner process timed out",
                    extra={"scan_id": str(scan_id), "timeout": timeout},
                )
                raise ScannerTimeoutException(
                    f"Scanner execution exceeded timeout of {timeout} seconds."
                ) from exc

        except Exception as e:
            if isinstance(e, ScannerTimeoutException):
                raise

            logger.exception(
                "Unexpected error during scanner subprocess execution",
                extra={"scan_id": str(scan_id)},
            )
            status = ExecutionStatus.ERROR
            raise ScannerExecutionException(
                f"Scanner process execution failed: {e}"
            ) from e

        finally:
            duration = time.time() - start_time

        return ScanArtifact(
            scan_id=scan_id,
            scanner_type=scanner_type,
            execution_status=status,
            exit_code=exit_code,
            execution_duration_seconds=duration,
            stdout=stdout_data,
            stderr=stderr_data,
            output_path=output_path,
        )
