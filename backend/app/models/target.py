from sqlalchemy import Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import TargetType
from app.database.base import Base, TimestampMixin


class Target(Base, TimestampMixin):
    """Database model for scan targets.

    A target is an entity (IP, CIDR, Hostname) that can be scanned.
    The normalized target value must be unique to prevent redundant scanning.
    """

    __tablename__ = "targets"

    # The actual string representation of the target (e.g. "192.168.1.10", "example.com")
    # This must be stored in its normalized form.
    target: Mapped[str] = mapped_column(
        String(253), unique=True, index=True, nullable=False
    )

    # Classification of the target to aid in validation and scanner configuration
    target_type: Mapped[TargetType] = mapped_column(Enum(TargetType), nullable=False)

    __table_args__ = (Index("ix_targets_created_at", "created_at"),)
