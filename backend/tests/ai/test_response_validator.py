import json

import pytest

from app.ai.response_validator import validate_response
from app.core.exceptions import InvalidAIResponseException

VALID_PAYLOAD = {
    "summary": "Outdated OpenSSH exposes known vulnerabilities.",
    "explanation": "The detected OpenSSH version is affected by known CVEs.",
    "remediation_steps": ["Upgrade OpenSSH to the latest stable release."],
    "validation_steps": ["Re-scan the host and confirm the version banner updated."],
    "cautions": ["Schedule the upgrade during a maintenance window."],
}


def test_validate_response_accepts_valid_json():
    result = validate_response(json.dumps(VALID_PAYLOAD))
    assert result.summary == VALID_PAYLOAD["summary"]
    assert result.remediation_steps == VALID_PAYLOAD["remediation_steps"]


def test_validate_response_accepts_markdown_json_code_fence():
    wrapped = f"```json\n{json.dumps(VALID_PAYLOAD)}\n```"
    result = validate_response(wrapped)
    assert result.summary == VALID_PAYLOAD["summary"]


def test_validate_response_accepts_bare_code_fence_without_json_tag():
    wrapped = f"```\n{json.dumps(VALID_PAYLOAD)}\n```"
    result = validate_response(wrapped)
    assert result.summary == VALID_PAYLOAD["summary"]


def test_validate_response_rejects_empty_response():
    with pytest.raises(InvalidAIResponseException):
        validate_response("")
    with pytest.raises(InvalidAIResponseException):
        validate_response("   ")


def test_validate_response_rejects_malformed_json():
    with pytest.raises(InvalidAIResponseException):
        validate_response("{not valid json")


def test_validate_response_rejects_arbitrary_text():
    with pytest.raises(InvalidAIResponseException):
        validate_response(
            "Sure! Here is some remediation advice for your vulnerability."
        )


def test_validate_response_rejects_missing_required_fields():
    payload = dict(VALID_PAYLOAD)
    del payload["remediation_steps"]
    with pytest.raises(InvalidAIResponseException):
        validate_response(json.dumps(payload))


def test_validate_response_rejects_wrong_field_types():
    payload = dict(VALID_PAYLOAD)
    payload["remediation_steps"] = "just do it"
    with pytest.raises(InvalidAIResponseException):
        validate_response(json.dumps(payload))


def test_validate_response_rejects_empty_required_string():
    payload = dict(VALID_PAYLOAD)
    payload["summary"] = ""
    with pytest.raises(InvalidAIResponseException):
        validate_response(json.dumps(payload))


def test_validate_response_rejects_empty_remediation_steps_list():
    payload = dict(VALID_PAYLOAD)
    payload["remediation_steps"] = []
    with pytest.raises(InvalidAIResponseException):
        validate_response(json.dumps(payload))


def test_validate_response_rejects_blank_step_entries():
    payload = dict(VALID_PAYLOAD)
    payload["remediation_steps"] = ["   "]
    with pytest.raises(InvalidAIResponseException):
        validate_response(json.dumps(payload))


def test_validate_response_rejects_oversized_step_collection():
    payload = dict(VALID_PAYLOAD)
    payload["remediation_steps"] = [f"Step {i}" for i in range(25)]
    with pytest.raises(InvalidAIResponseException):
        validate_response(json.dumps(payload))


def test_validate_response_optional_fields_default_when_absent():
    payload = {
        "summary": VALID_PAYLOAD["summary"],
        "explanation": VALID_PAYLOAD["explanation"],
        "remediation_steps": VALID_PAYLOAD["remediation_steps"],
    }
    result = validate_response(json.dumps(payload))
    assert result.validation_steps == []
    assert result.cautions == []


def test_validate_response_does_not_execute_or_eval_content():
    """Even if the AI output contains code-like text, it must be treated as
    inert string data, never executed or evaluated.
    """
    payload = dict(VALID_PAYLOAD)
    payload["summary"] = "__import__('os').system('id')"
    result = validate_response(json.dumps(payload))
    assert result.summary == "__import__('os').system('id')"
