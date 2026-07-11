from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from app.database.base import Base, TimestampMixin


class Asset(Base, TimestampMixin):
    """Database model for discovered assets."""
    __tablename__ = "assets"

    # Unique inventory identity: IPv4 address
    ipv4: Mapped[str] = mapped_column(
        String(45), unique=True, index=True, nullable=False
    )
    
    # Optional hostname
    hostname: Mapped[str | None] = mapped_column(
        String(253), nullable=True
    )
    
    # Optional operating system details
    operating_system: Mapped[str | None] = mapped_column(
        String(253), nullable=True
    )

    # Relationships
    services: Mapped[List["NetworkService"]] = relationship(
        "NetworkService", back_populates="asset", cascade="all, delete-orphan", lazy="selectin"
    )
