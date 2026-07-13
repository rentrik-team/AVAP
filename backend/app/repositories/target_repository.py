import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateException
from app.models.target import Target


class TargetRepository:
    """Repository for managing Target database operations.

    Contains only database access logic. No business validation.
    """

    def __init__(self, session: Session):
        self.session = session

    def create(self, target: Target) -> Target:
        """Add a new target to the session and flush, without committing.

        Args:
            target: The Target model instance to persist.

        Returns:
            The flushed Target instance (has an ID within the open transaction).

        Raises:
            DuplicateException: If a target with the same value already exists.
        """
        try:
            self.session.add(target)
            self.session.flush()
            return target
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateException(
                message=f"Target '{target.target}' already exists.",
                details={"target": target.target},
            ) from exc

    def get_by_id(self, target_id: uuid.UUID) -> Target | None:
        """Retrieve a target by its ID.

        Args:
            target_id: The UUID of the target.

        Returns:
            The Target instance if found, None otherwise.
        """
        stmt = select(Target).where(Target.id == target_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_value(self, target_value: str) -> Target | None:
        """Retrieve a target by its normalized value.

        Args:
            target_value: The normalized string value of the target.

        Returns:
            The Target instance if found, None otherwise.
        """
        stmt = select(Target).where(Target.target == target_value)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_all(self, skip: int = 0, limit: int = 50) -> tuple[Sequence[Target], int]:
        """Retrieve a paginated list of all targets.

        Args:
            skip: Number of records to skip (offset).
            limit: Maximum number of records to return.

        Returns:
            A tuple containing (list_of_targets, total_count).
        """
        # Get items
        stmt = (
            select(Target).offset(skip).limit(limit).order_by(Target.created_at.desc())
        )
        items = self.session.execute(stmt).scalars().all()

        # Get total count (for pagination)
        count_stmt = select(func.count()).select_from(Target)
        total = self.session.execute(count_stmt).scalar() or 0

        return items, total

    def update(self, target: Target) -> Target:
        """Flush pending changes to an existing target, without committing.

        Args:
            target: The updated Target instance.

        Returns:
            The flushed Target instance.

        Raises:
            DuplicateException: If updating causes a unique constraint violation.
        """
        try:
            self.session.flush()
            return target
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateException(
                message=f"Target '{target.target}' already exists.",
                details={"target": target.target},
            ) from exc

    def delete(self, target: Target) -> None:
        """Mark a target for deletion and flush, without committing.

        Args:
            target: The Target instance to delete.
        """
        self.session.delete(target)
        self.session.flush()
