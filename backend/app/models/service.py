from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from app.database.base import Base, TimestampMixin


class NetworkService(Base, TimestampMixin):
    """Database model for discovered network services on an asset."""
    __tablename__ = "services"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    port: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    
    protocol: Mapped[str] = mapped_column(
        String(10), nullable=False
    )
    
    service_name: Mapped[str] = mapped_column(
        String(50), nullable=False, default="unknown"
    )
    
    product: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    
    version: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )
    
    extra_info: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # Relationships
    asset: Mapped["Asset"] = relationship("Asset", back_populates="services")

    __table_args__ = (
        UniqueConstraint("asset_id", "port", "protocol", name="uq_services_asset_port_proto"),
    )
