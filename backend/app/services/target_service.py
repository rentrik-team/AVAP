import logging
import uuid
from collections.abc import Sequence

from app.audit.context import AuditContext
from app.core.enums import (
    AuditEventCategory,
    AuditEventType,
    AuditOutcome,
    AuditResourceType,
    TargetType,
)
from app.core.exceptions import NotFoundException, ValidationException
from app.core.security import (
    is_valid_hostname,
    is_valid_ipv4,
    is_valid_ipv4_cidr,
    normalize_target_value,
)
from app.models.target import Target
from app.repositories.target_repository import TargetRepository
from app.schemas.target import CreateTargetRequest, UpdateTargetRequest
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class TargetService:
    """Business logic for Target management.

    Responsible for validating, normalizing, and deduplicating scan targets.
    """

    def __init__(self, repository: TargetRepository, audit_service: AuditService):
        self.repository = repository
        self.audit_service = audit_service

    def _commit_with_audit(
        self,
        event_type: AuditEventType,
        context: AuditContext,
        resource_id: uuid.UUID,
        metadata: dict | None = None,
    ) -> None:
        """Append a TARGET-category audit event in the same transaction as
        the already-flushed target mutation, then commit both atomically.

        Shared transaction (preferred pattern, see backend.md → "Audit
        event transaction pattern"): if the audit insert or its metadata
        validation fails, this raises before commit and the entire
        mutation (repository flush included) rolls back rather than being
        reported as successful.
        """
        try:
            self.audit_service.append_event(
                event_type=event_type,
                category=AuditEventCategory.TARGET,
                outcome=AuditOutcome.SUCCESS,
                context=context,
                resource_type=AuditResourceType.TARGET,
                resource_id=resource_id,
                metadata=metadata,
            )
            self.repository.session.commit()
        except Exception:
            self.repository.session.rollback()
            logger.error(
                "Target mutation failed to commit; transaction rolled back.",
                extra={"event_type": event_type.value, "resource_id": str(resource_id)},
                exc_info=True,
            )
            raise

    def _determine_target_type(self, target_value: str) -> TargetType:
        """Classify a target string into its TargetType enum.

        Args:
            target_value: The target string.

        Returns:
            The TargetType enum value.

        Raises:
            ValidationException: If the target does not match any supported type.
        """
        if is_valid_ipv4(target_value):
            return TargetType.IPV4

        if is_valid_ipv4_cidr(target_value):
            return TargetType.CIDR

        if is_valid_hostname(target_value):
            return TargetType.HOSTNAME

        raise ValidationException(
            message=f"Unsupported or invalid target format: '{target_value}'",
            details={
                "target": target_value,
                "allowed_formats": ["IPv4", "CIDR", "Hostname"],
            },
        )

    def create_target(
        self, request: CreateTargetRequest, audit_context: AuditContext | None = None
    ) -> Target:
        """Process and persist a new target.

        Args:
            request: The target creation request.

        Returns:
            The persisted Target model.
        """
        # 1. Normalize
        normalized_value = normalize_target_value(request.target)

        # 2. Validate format and classify type
        target_type = self._determine_target_type(normalized_value)

        # 3. Prevent duplicates
        existing = self.repository.get_by_value(normalized_value)
        if existing:
            # Re-throw as validation exception to match business rules?
            # Or rely on repository's DuplicateException?
            # Since repository throws DuplicateException on IntegrityError,
            # we can proactively throw it here to avoid burning sequence numbers,
            # but raising it directly keeps things clean.
            from app.core.exceptions import DuplicateException

            raise DuplicateException(
                message=f"Target '{normalized_value}' already exists.",
                details={"target": normalized_value},
            )

        # 4. Construct model and persist
        target = Target(target=normalized_value, target_type=target_type)
        created = self.repository.create(target)

        self._commit_with_audit(
            event_type=AuditEventType.TARGET_CREATED,
            context=audit_context or AuditContext.system(),
            resource_id=created.id,
            metadata={"target_type": created.target_type.value},
        )
        return created

    def get_target(self, target_id: uuid.UUID) -> Target:
        """Retrieve a single target by ID.

        Args:
            target_id: The target's UUID.

        Returns:
            The Target model.

        Raises:
            NotFoundException: If the target does not exist.
        """
        target = self.repository.get_by_id(target_id)
        if not target:
            raise NotFoundException(message=f"Target not found: {target_id}")
        return target

    def get_all_targets(
        self, skip: int = 0, limit: int = 50
    ) -> tuple[Sequence[Target], int]:
        """Retrieve all targets with pagination.

        Args:
            skip: Offset.
            limit: Max results.

        Returns:
            Tuple of (targets, total_count).
        """
        return self.repository.get_all(skip=skip, limit=limit)

    def update_target(
        self,
        target_id: uuid.UUID,
        request: UpdateTargetRequest,
        audit_context: AuditContext | None = None,
    ) -> Target:
        """Update an existing target.

        Args:
            target_id: The UUID of the target to update.
            request: The update request data.

        Returns:
            The updated Target model.
        """
        # Retrieve existing
        target = self.get_target(target_id)

        # Normalize and validate new value
        normalized_value = normalize_target_value(request.target)
        target_type = self._determine_target_type(normalized_value)

        # Check for duplicates on update (excluding self)
        existing = self.repository.get_by_value(normalized_value)
        if existing and existing.id != target_id:
            from app.core.exceptions import DuplicateException

            raise DuplicateException(
                message=f"Target '{normalized_value}' already exists.",
                details={"target": normalized_value},
            )

        # Update
        target.target = normalized_value
        target.target_type = target_type

        updated = self.repository.update(target)

        self._commit_with_audit(
            event_type=AuditEventType.TARGET_UPDATED,
            context=audit_context or AuditContext.system(),
            resource_id=updated.id,
            metadata={"target_type": updated.target_type.value},
        )
        return updated

    def delete_target(
        self, target_id: uuid.UUID, audit_context: AuditContext | None = None
    ) -> None:
        """Delete a target.

        Args:
            target_id: The UUID of the target.
        """
        target = self.get_target(target_id)
        target_id_value = target.id
        target_type_value = target.target_type.value
        self.repository.delete(target)

        self._commit_with_audit(
            event_type=AuditEventType.TARGET_DELETED,
            context=audit_context or AuditContext.system(),
            resource_id=target_id_value,
            metadata={"target_type": target_type_value},
        )
