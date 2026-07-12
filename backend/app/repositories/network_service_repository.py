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
