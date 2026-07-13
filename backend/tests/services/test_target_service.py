import uuid
from unittest.mock import Mock

import pytest

from app.core.enums import TargetType
from app.core.exceptions import (
    DuplicateException,
    NotFoundException,
    ValidationException,
)
from app.models.target import Target
from app.schemas.target import CreateTargetRequest, UpdateTargetRequest
from app.services.target_service import TargetService


@pytest.fixture
def mock_repo():
    return Mock()


@pytest.fixture
def service(mock_repo):
    return TargetService(repository=mock_repo, audit_service=Mock())


class TestTargetClassificationAndValidation:
    @pytest.mark.parametrize(
        "target, expected_type",
        [
            ("192.168.1.1", TargetType.IPV4),
            ("8.8.8.8", TargetType.IPV4),
            ("10.0.0.0/8", TargetType.CIDR),
            ("192.168.1.0/24", TargetType.CIDR),
            ("example.com", TargetType.HOSTNAME),
            ("www.google.com", TargetType.HOSTNAME),
            ("internal-server", TargetType.HOSTNAME),
            ("host.internal.corp", TargetType.HOSTNAME),
        ],
    )
    def test_determine_target_type_valid(self, service, target, expected_type):
        assert service._determine_target_type(target) == expected_type

    @pytest.mark.parametrize(
        "invalid_target",
        [
            "999.999.999.999",  # Invalid IPv4
            "192.168.1.1/33",  # Invalid CIDR prefix
            "192.168.1.1/abc",  # Invalid CIDR
            "not@host.com",  # Invalid hostname character
            "example..com",  # Empty label
            "-invalid.com",  # Leading hyphen
            "",  # Empty
        ],
    )
    def test_determine_target_type_invalid(self, service, invalid_target):
        with pytest.raises(ValidationException):
            service._determine_target_type(invalid_target)


class TestCreateTarget:
    def test_create_valid_target(self, service, mock_repo):
        request = CreateTargetRequest(target=" EXAMPLE.com  ")
        mock_repo.get_by_value.return_value = None

        # Mock repository create return
        expected_target = Target(target="example.com", target_type=TargetType.HOSTNAME)
        mock_repo.create.return_value = expected_target

        result = service.create_target(request)

        # Verify normalization and classification
        assert result.target == "example.com"
        assert result.target_type == TargetType.HOSTNAME

        mock_repo.get_by_value.assert_called_once_with("example.com")
        # Ensure we passed a correctly configured Target to the repo
        created_arg = mock_repo.create.call_args[0][0]
        assert created_arg.target == "example.com"
        assert created_arg.target_type == TargetType.HOSTNAME

    def test_create_duplicate_target(self, service, mock_repo):
        request = CreateTargetRequest(target="192.168.1.1")
        mock_repo.get_by_value.return_value = Target(
            id=uuid.uuid4(), target="192.168.1.1"
        )

        with pytest.raises(DuplicateException):
            service.create_target(request)

        mock_repo.create.assert_not_called()


class TestUpdateTarget:
    def test_update_valid_target(self, service, mock_repo):
        target_id = uuid.uuid4()
        existing = Target(
            id=target_id, target="old.com", target_type=TargetType.HOSTNAME
        )

        mock_repo.get_by_id.return_value = existing
        mock_repo.get_by_value.return_value = None
        mock_repo.update.return_value = (
            existing  # Repo typically returns the same updated instance
        )

        request = UpdateTargetRequest(target="new.com")
        result = service.update_target(target_id, request)

        assert result.target == "new.com"
        assert result.target_type == TargetType.HOSTNAME
        mock_repo.update.assert_called_once()

    def test_update_target_not_found(self, service, mock_repo):
        mock_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException):
            service.update_target(uuid.uuid4(), UpdateTargetRequest(target="1.1.1.1"))

    def test_update_target_duplicate_conflict(self, service, mock_repo):
        target_id = uuid.uuid4()
        existing = Target(id=target_id, target="old.com")
        conflict = Target(id=uuid.uuid4(), target="new.com")

        mock_repo.get_by_id.return_value = existing
        mock_repo.get_by_value.return_value = conflict

        with pytest.raises(DuplicateException):
            service.update_target(target_id, UpdateTargetRequest(target="new.com"))

    def test_update_same_target_value_is_allowed(self, service, mock_repo):
        # Updating to the same value shouldn't trigger duplicate exception
        target_id = uuid.uuid4()
        existing = Target(
            id=target_id, target="192.168.1.1", target_type=TargetType.IPV4
        )

        mock_repo.get_by_id.return_value = existing
        # get_by_value returns the SAME record
        mock_repo.get_by_value.return_value = existing
        mock_repo.update.return_value = existing

        result = service.update_target(
            target_id, UpdateTargetRequest(target="192.168.1.1")
        )

        assert result.target == "192.168.1.1"
        mock_repo.update.assert_called_once()
