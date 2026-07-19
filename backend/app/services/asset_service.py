import uuid
from collections.abc import Sequence

from app.core.exceptions import NotFoundException
from app.models.asset import Asset
from app.repositories.asset_repository import AssetRepository


class AssetService:
    """Business logic for Asset queries and lifecycle management.

    Owns the transaction boundary for asset mutations; the repository only
    flushes.
    """

    def __init__(self, repository: AssetRepository):
        self.repository = repository

    def get_all_assets(
        self,
        skip: int = 0,
        limit: int = 50,
        ip: str | None = None,
        hostname: str | None = None,
        port: int | None = None,
        cve: str | None = None,
        target_id: uuid.UUID | None = None,
    ) -> tuple[Sequence[Asset], int]:
        """Retrieve a paginated, filtered list of assets."""
        return self.repository.get_all(
            skip=skip,
            limit=limit,
            ip=ip,
            hostname=hostname,
            port=port,
            cve=cve,
            target_id=target_id,
        )

    def get_asset(self, asset_id: uuid.UUID) -> Asset:
        """Retrieve a single asset by ID, including its services.

        Raises:
            NotFoundException: If the asset does not exist.
        """
        asset = self.repository.get_by_id(asset_id)
        if not asset:
            raise NotFoundException(f"Asset with ID {asset_id} not found.")
        return asset

    def delete_asset(self, asset_id: uuid.UUID) -> None:
        """Delete an asset and commit the transaction.

        Raises:
            NotFoundException: If the asset does not exist.
        """
        asset = self.get_asset(asset_id)
        self.repository.delete(asset)
        self.repository.session.commit()
