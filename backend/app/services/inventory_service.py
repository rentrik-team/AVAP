import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import ScanStatus
from app.core.exceptions import NotFoundException, ParserException
from app.models.asset import Asset
from app.models.service import NetworkService
from app.models.vulnerability import Vulnerability
from app.models.scan_finding import ScanFinding
from app.repositories.asset_repository import AssetRepository
from app.repositories.vulnerability_repository import VulnerabilityRepository
from app.repositories.scan_repository import ScanRepository
from app.parsers.models import AssessmentPackage, ParsedHost, ParsedService, ParsedVulnerability

logger = logging.getLogger(__name__)


class InventoryService:
    """Service layer for Asset & Vulnerability Management orchestration."""

    def __init__(
        self,
        session: Session,
        asset_repository: AssetRepository,
        vulnerability_repository: VulnerabilityRepository,
        scan_repository: ScanRepository
    ):
        self.session = session
        self.asset_repository = asset_repository
        self.vulnerability_repository = vulnerability_repository
        self.scan_repository = scan_repository

    def _upsert_asset(self, host: ParsedHost) -> Asset:
        """Upsert an asset based on IPv4 address."""
        existing_asset = self.asset_repository.get_by_ip(host.ipv4)
        
        if existing_asset:
            # Update hostname if meaningful data is provided
            if host.hostname and host.hostname.strip():
                existing_asset.hostname = host.hostname.strip()
            
            # Update OS if meaningful data is provided
            if host.operating_system and host.operating_system.strip():
                existing_asset.operating_system = host.operating_system.strip()
            
            self.session.flush()
            return existing_asset
        else:
            new_asset = Asset(
                ipv4=host.ipv4,
                hostname=host.hostname.strip() if host.hostname else None,
                operating_system=host.operating_system.strip() if host.operating_system else None
            )
            self.asset_repository.create(new_asset)
            return new_asset

    def _upsert_service(self, asset_id: uuid.UUID, parsed_service: ParsedService) -> NetworkService:
        """Upsert a NetworkService on a specific asset using asset_id + port + protocol."""
        stmt = select(NetworkService).where(
            NetworkService.asset_id == asset_id,
            NetworkService.port == parsed_service.port,
            NetworkService.protocol == parsed_service.protocol
        )
        existing_service = self.session.execute(stmt).scalar_one_or_none()

        if existing_service:
            # Update service info if meaningful data is provided
            if parsed_service.service_name and parsed_service.service_name != "unknown":
                existing_service.service_name = parsed_service.service_name
            if parsed_service.product and parsed_service.product.strip():
                existing_service.product = parsed_service.product.strip()
            if parsed_service.version and parsed_service.version.strip():
                existing_service.version = parsed_service.version.strip()
            if parsed_service.extra_info and parsed_service.extra_info.strip():
                existing_service.extra_info = parsed_service.extra_info.strip()
                
            self.session.flush()
            return existing_service
        else:
            new_service = NetworkService(
                asset_id=asset_id,
                port=parsed_service.port,
                protocol=parsed_service.protocol,
                service_name=parsed_service.service_name,
                product=parsed_service.product.strip() if parsed_service.product else None,
                version=parsed_service.version.strip() if parsed_service.version else None,
                extra_info=parsed_service.extra_info.strip() if parsed_service.extra_info else None
            )
            self.session.add(new_service)
            self.session.flush()
            return new_service

    def _upsert_vulnerability(self, parsed_vuln: ParsedVulnerability) -> Vulnerability:
        """Upsert a Vulnerability using name + cve."""
        norm_name = parsed_vuln.name.strip()
        norm_cve = parsed_vuln.cve.strip().upper() if parsed_vuln.cve else None

        existing_vuln = self.vulnerability_repository.get_by_name_and_cve(
            norm_name, norm_cve
        )

        if existing_vuln:
            # Reuse the existing record
            return existing_vuln
        else:
            new_vuln = Vulnerability(
                name=norm_name,
                severity_score=parsed_vuln.severity_score,
                severity_rating=parsed_vuln.severity_rating,
                description=parsed_vuln.description,
                cve=norm_cve
            )
            self.vulnerability_repository.create(new_vuln)
            return new_vuln

    def _create_finding_if_not_exists(
        self,
        scan_id: uuid.UUID,
        asset_id: uuid.UUID,
        vulnerability_id: Optional[uuid.UUID],
        service_id: Optional[uuid.UUID]
    ) -> None:
        """Create a ScanFinding linking the entities, preventing duplicates (handling nulls)."""
        stmt = select(ScanFinding).where(
            ScanFinding.scan_id == scan_id,
            ScanFinding.asset_id == asset_id
        )

        if vulnerability_id is None:
            stmt = stmt.where(ScanFinding.vulnerability_id.is_(None))
        else:
            stmt = stmt.where(ScanFinding.vulnerability_id == vulnerability_id)

        if service_id is None:
            stmt = stmt.where(ScanFinding.service_id.is_(None))
        else:
            stmt = stmt.where(ScanFinding.service_id == service_id)

        existing_finding = self.session.execute(stmt).scalar_one_or_none()

        if not existing_finding:
            finding = ScanFinding(
                scan_id=scan_id,
                asset_id=asset_id,
                vulnerability_id=vulnerability_id,
                service_id=service_id
            )
            self.session.add(finding)
            self.session.flush()

    def process_assessment_package(self, package: AssessmentPackage) -> None:
        """Process assessment package inside an ACID transaction."""
        # 1. Resolve related ScanJob
        scan_job = self.scan_repository.get_by_id(package.scan_id)
        if not scan_job:
            raise NotFoundException(f"Scan job with ID {package.scan_id} not found.")

        logger.info(
            "Processing assessment package",
            extra={
                "scan_id": str(package.scan_id),
                "scanner": package.scanner_type.value,
                "hosts": len(package.parsed_hosts)
            }
        )

        try:
            # Process hosts sequentially
            for host in package.parsed_hosts:
                # 2. Upsert Asset
                asset = self._upsert_asset(host)

                # Process services for this host
                for parsed_service in host.services:
                    # 3. Upsert NetworkService
                    service = self._upsert_service(asset.id, parsed_service)

                    # Check if there are vulnerabilities associated with this service
                    if parsed_service.vulnerabilities:
                        for parsed_vuln in parsed_service.vulnerabilities:
                            # 4. Upsert Vulnerability
                            vuln = self._upsert_vulnerability(parsed_vuln)
                            
                            # 5. Create ScanFinding linking scan, asset, vuln, service
                            self._create_finding_if_not_exists(
                                scan_id=package.scan_id,
                                asset_id=asset.id,
                                vulnerability_id=vuln.id,
                                service_id=service.id
                            )
                    else:
                        # Create ScanFinding linking scan, asset, service (without vulnerability)
                        self._create_finding_if_not_exists(
                            scan_id=package.scan_id,
                            asset_id=asset.id,
                            vulnerability_id=None,
                            service_id=service.id
                        )

            # 6. Update ScanJob Status to COMPLETED
            scan_job.status = ScanStatus.COMPLETED
            now = datetime.now(timezone.utc)
            scan_job.completed_at = now
            if scan_job.started_at:
                # Convert timezone if needed (database uses tz aware)
                started = scan_job.started_at.replace(tzinfo=timezone.utc) if scan_job.started_at.tzinfo is None else scan_job.started_at
                scan_job.execution_duration = (now - started).total_seconds()

            self.session.add(scan_job)
            self.session.flush()

            # 7. Commit transaction
            self.session.commit()
            logger.info("Assessment package processed successfully", extra={"scan_id": str(package.scan_id)})

        except Exception as e:
            # ACID Rollback on failure
            logger.error(
                f"Failed to process assessment package: {e}. Rolling back transaction.",
                extra={"scan_id": str(package.scan_id)},
                exc_info=True
            )
            self.session.rollback()

            # Transition ScanJob to FAILED in a separate clean transaction
            try:
                # Fetch scan job again to reload state
                failed_job = self.scan_repository.get_by_id(package.scan_id)
                if failed_job:
                    failed_job.status = ScanStatus.FAILED
                    failed_job.failure_reason = str(e)
                    failed_job.completed_at = datetime.now(timezone.utc)
                    self.session.add(failed_job)
                    self.session.commit()
            except Exception as rollback_err:
                logger.exception(
                    f"Failed to transition scan job {package.scan_id} to FAILED status",
                    extra={"scan_id": str(package.scan_id)}
                )

            # Preserve and raise the original exception context
            raise e
