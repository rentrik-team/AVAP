import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.service import NetworkService


class NetworkServiceRepository:
    """Read-only repository for querying persisted network services."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, service_id: uuid.UUID) -> NetworkService | None:
        """Retrieve a network service by its ID."""
        stmt = select(NetworkService).where(NetworkService.id == service_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_asset_port_protocol(
        self, asset_id: uuid.UUID, port: int, protocol: str
    ) -> NetworkService | None:
        """Retrieve a network service by its owning asset, port, and protocol."""
        stmt = select(NetworkService).where(
            NetworkService.asset_id == asset_id,
            NetworkService.port == port,
            NetworkService.protocol == protocol,
        )
        return self.session.execute(stmt).scalar_one_or_none()
