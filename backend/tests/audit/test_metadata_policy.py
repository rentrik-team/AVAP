import pytest

from app.audit.metadata_policy import (
    MAX_KEYS_PER_LEVEL,
    MAX_STRING_VALUE_LENGTH,
    validate_metadata,
)
from app.core.exceptions import UnsafeAuditMetadataException


def test_none_normalizes_to_empty_dict():
    assert validate_metadata(None) == {}


def test_safe_scalar_metadata_accepted():
    metadata = {
        "risk_score": 8.0,
        "risk_level": "HIGH",
        "provider": "openrouter",
        "finding_count": 3,
        "included": True,
        "note": None,
    }
    assert validate_metadata(metadata) == metadata


def test_one_level_nested_dict_accepted():
    metadata = {"context": {"scanner_type": "OPENVAS"}}
    assert validate_metadata(metadata) == metadata


@pytest.mark.parametrize(
    "key",
    [
        "authorization",
        "Authorization",
        "AUTHORIZATION",
        "password",
        "passwd",
        "secret",
        "secret_key",
        "token",
        "access_token",
        "api_key",
        "apikey",
        "cookie",
        "set-cookie",
        "database_url",
        "private_key",
    ],
)
def test_forbidden_key_rejected_case_insensitively(key):
    with pytest.raises(UnsafeAuditMetadataException):
        validate_metadata({key: "value"})


def test_nested_forbidden_key_rejected():
    with pytest.raises(UnsafeAuditMetadataException):
        validate_metadata({"context": {"authorization": "Bearer xyz"}})


def test_metadata_must_be_a_dict():
    with pytest.raises(UnsafeAuditMetadataException):
        validate_metadata("not a dict")  # type: ignore[arg-type]


def test_non_string_key_rejected():
    with pytest.raises(UnsafeAuditMetadataException):
        validate_metadata({1: "value"})


def test_oversized_string_value_rejected():
    with pytest.raises(UnsafeAuditMetadataException):
        validate_metadata({"note": "x" * (MAX_STRING_VALUE_LENGTH + 1)})


def test_string_value_at_exact_limit_accepted():
    metadata = {"note": "x" * MAX_STRING_VALUE_LENGTH}
    assert validate_metadata(metadata) == metadata


def test_too_many_keys_rejected():
    metadata = {f"key_{i}": i for i in range(MAX_KEYS_PER_LEVEL + 1)}
    with pytest.raises(UnsafeAuditMetadataException):
        validate_metadata(metadata)


def test_excessive_nesting_rejected():
    # depth 1 (top) -> depth 2 (nested) -> depth 3 (too deep)
    metadata = {"level1": {"level2": {"level3": "too deep"}}}
    with pytest.raises(UnsafeAuditMetadataException):
        validate_metadata(metadata)


def test_unsupported_value_type_rejected():
    class _Unsupported:
        pass

    with pytest.raises(UnsafeAuditMetadataException):
        validate_metadata({"bad": _Unsupported()})


def test_orm_object_rejected():
    from app.models.target import Target

    target = Target(target="10.0.0.1", target_type="IPV4")
    with pytest.raises(UnsafeAuditMetadataException):
        validate_metadata({"target": target})


def test_exception_object_rejected():
    with pytest.raises(UnsafeAuditMetadataException):
        validate_metadata({"error": ValueError("boom")})


def test_list_value_rejected():
    """Lists are not a supported metadata value type in this policy: audit
    metadata is restricted to scalars plus one level of dict nesting."""
    with pytest.raises(UnsafeAuditMetadataException):
        validate_metadata({"steps": ["one", "two"]})


def test_key_too_long_rejected():
    with pytest.raises(UnsafeAuditMetadataException):
        validate_metadata({"k" * 200: "value"})
