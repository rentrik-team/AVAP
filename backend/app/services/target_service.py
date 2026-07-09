import uuid
from typing import Sequence

from app.core.enums import TargetType
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


class TargetService:
    """Business logic for Target management.
    
    Responsible for validating, normalizing, and deduplicating scan targets.
    """
    
    def __init__(self, repository: TargetRepository):
        self.repository = repository

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
            details={"target": target_value, "allowed_formats": ["IPv4", "CIDR", "Hostname"]}
        )

    def create_target(self, request: CreateTargetRequest) -> Target:
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
                details={"target": normalized_value}
            )
            
        # 4. Construct model and persist
        target = Target(target=normalized_value, target_type=target_type)
        return self.repository.create(target)

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

    def get_all_targets(self, skip: int = 0, limit: int = 50) -> tuple[Sequence[Target], int]:
        """Retrieve all targets with pagination.
        
        Args:
            skip: Offset.
            limit: Max results.
            
        Returns:
            Tuple of (targets, total_count).
        """
        return self.repository.get_all(skip=skip, limit=limit)

    def update_target(self, target_id: uuid.UUID, request: UpdateTargetRequest) -> Target:
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
                details={"target": normalized_value}
            )
            
        # Update
        target.target = normalized_value
        target.target_type = target_type
        
        return self.repository.update(target)

    def delete_target(self, target_id: uuid.UUID) -> None:
        """Delete a target.
        
        Args:
            target_id: The UUID of the target.
        """
        target = self.get_target(target_id)
        self.repository.delete(target)
