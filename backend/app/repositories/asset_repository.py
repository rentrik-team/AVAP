import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.asset import Asset
from app.models.scan_finding import ScanFinding
from app.models.service import NetworkService
from app.models.vulnerability import Vulnerability


class AssetRepository:
    """Repository for managing Asset database operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, asset: Asset) -> Asset:
        """Add a new asset to the session without committing."""
        self.session.add(asset)
        self.session.flush()
        return asset

    def get_by_id(self, asset_id: uuid.UUID) -> Asset | None:
        """Retrieve an asset by its ID, eager loading its services."""
        stmt = (
            select(Asset)
            .where(Asset.id == asset_id)
            .options(selectinload(Asset.services))
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_ip(self, ipv4: str) -> Asset | None:
        """Retrieve an asset by its IPv4 address."""
        stmt = (
            select(Asset)
            .where(Asset.ipv4 == ipv4)
            .options(selectinload(Asset.services))
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 50,
        ip: str | None = None,
        hostname: str | None = None,
        port: int | None = None,
        cve: str | None = None,
    ) -> tuple[Sequence[Asset], int]:
        """Retrieve a paginated, filtered list of assets along with the total count.

        Uses a subquery strategy for join-based filters (port, cve) to avoid
        GROUP BY issues and ensure PostgreSQL compatibility.
        """
        # Build an ID subquery when join-based filters are needed
        needs_subquery = port is not None or cve is not None

        if needs_subquery:
            # Subquery: select distinct asset IDs matching the join filters
            id_subq = select(Asset.id.distinct())

            if port is not None:
                id_subq = id_subq.join(Asset.services).where(
                    NetworkService.port == port
                )

            if cve is not None:
                id_subq = (
                    id_subq.join(ScanFinding, ScanFinding.asset_id == Asset.id)
                    .join(
                        Vulnerability, ScanFinding.vulnerability_id == Vulnerability.id
                    )
                    .where(Vulnerability.cve.ilike(f"%{cve}%"))
                )

            # Add simple column filters to subquery too
            if ip:
                id_subq = id_subq.where(Asset.ipv4 == ip)
            if hostname:
                id_subq = id_subq.where(Asset.hostname.ilike(f"%{hostname}%"))

            id_subquery = id_subq.subquery()

            # Main query filters on the subquery result
            stmt = (
                select(Asset)
                .where(Asset.id.in_(select(id_subquery)))
                .options(selectinload(Asset.services))
            )
            count_stmt = select(func.count()).select_from(id_subquery)
        else:
            # Simple query — no joins needed
            stmt = select(Asset).options(selectinload(Asset.services))
            count_stmt = select(func.count(Asset.id))

            if ip:
                stmt = stmt.where(Asset.ipv4 == ip)
                count_stmt = count_stmt.where(Asset.ipv4 == ip)
            if hostname:
                stmt = stmt.where(Asset.hostname.ilike(f"%{hostname}%"))
                count_stmt = count_stmt.where(Asset.hostname.ilike(f"%{hostname}%"))

        # Execute count
        total = self.session.execute(count_stmt).scalar() or 0

        # Execute paginated items
        stmt = stmt.offset(skip).limit(limit).order_by(Asset.created_at.desc())
        items = self.session.execute(stmt).scalars().all()

        return items, total

    def delete(self, asset: Asset) -> None:
        """Delete an asset from the session."""
        self.session.delete(asset)
        self.session.flush()
