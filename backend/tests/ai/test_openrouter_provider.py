from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.ai.provider import Prompt
from app.ai.providers.openrouter import OpenRouterProvider
from app.core.config import Settings
from app.core.exceptions import AIProviderConfigurationException, AIProviderException


def _settings(**overrides) -> Settings:
    defaults: dict[str, Any] = {
        "openrouter_api_key": "test-key",
        "openrouter_base_url": "https://openrouter.ai/api/v1",
        "openrouter_model": "test-model",
        "ai_request_timeout_seconds": 30,
        "ai_max_tokens": 1024,
    }
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)


def _mock_response(status_code=200, json_data=None):
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.json.return_value = json_data or {}
    return response


def test_openrouter_provider_requires_api_key():
    with pytest.raises(AIProviderConfigurationException):
        OpenRouterProvider(_settings(openrouter_api_key=""))


def test_openrouter_provider_success_extracts_content():
    provider = OpenRouterProvider(_settings())
    payload = {"choices": [{"message": {"content": '{"summary": "ok"}'}}]}

    with patch(
        "app.ai.providers.openrouter.httpx.post",
        return_value=_mock_response(200, payload),
    ):
        result = provider.generate(Prompt(system="sys", user="usr"))

    assert result.content == '{"summary": "ok"}'
    assert result.provider == "openrouter"
    assert result.model == "test-model"


def test_openrouter_provider_sends_authorization_and_no_leak():
    provider = OpenRouterProvider(_settings(openrouter_api_key="super-secret-key"))
    payload = {"choices": [{"message": {"content": "content"}}]}

    with patch(
        "app.ai.providers.openrouter.httpx.post",
        return_value=_mock_response(200, payload),
    ) as mock_post:
        provider.generate(Prompt(system="sys", user="usr"))

    _, kwargs = mock_post.call_args
    assert kwargs["headers"]["Authorization"] == "Bearer super-secret-key"


def test_openrouter_provider_timeout_translated_to_ai_exception():
    provider = OpenRouterProvider(_settings())
    with (
        patch(
            "app.ai.providers.openrouter.httpx.post",
            side_effect=httpx.TimeoutException("timed out"),
        ),
        pytest.raises(AIProviderException) as exc,
    ):
        provider.generate(Prompt(system="sys", user="usr"))
    assert "timed out" in str(exc.value).lower()


def test_openrouter_provider_network_failure_translated_to_ai_exception():
    provider = OpenRouterProvider(_settings())
    with (
        patch(
            "app.ai.providers.openrouter.httpx.post",
            side_effect=httpx.ConnectError("connection refused"),
        ),
        pytest.raises(AIProviderException),
    ):
        provider.generate(Prompt(system="sys", user="usr"))


def test_openrouter_provider_non_success_status_translated_to_ai_exception():
    provider = OpenRouterProvider(_settings())
    with (
        patch(
            "app.ai.providers.openrouter.httpx.post",
            return_value=_mock_response(401, {"error": "invalid api key"}),
        ),
        pytest.raises(AIProviderException) as exc,
    ):
        provider.generate(Prompt(system="sys", user="usr"))
    # The provider's raw error payload must never leak into the AVAP exception.
    assert "invalid api key" not in str(exc.value).lower()


def test_openrouter_provider_malformed_response_translated_to_ai_exception():
    provider = OpenRouterProvider(_settings())
    with (
        patch(
            "app.ai.providers.openrouter.httpx.post",
            return_value=_mock_response(200, {"unexpected": "shape"}),
        ),
        pytest.raises(AIProviderException),
    ):
        provider.generate(Prompt(system="sys", user="usr"))


def test_openrouter_provider_empty_response_translated_to_ai_exception():
    provider = OpenRouterProvider(_settings())
    payload = {"choices": [{"message": {"content": ""}}]}
    with (
        patch(
            "app.ai.providers.openrouter.httpx.post",
            return_value=_mock_response(200, payload),
        ),
        pytest.raises(AIProviderException),
    ):
        provider.generate(Prompt(system="sys", user="usr"))


def test_openrouter_provider_does_not_leak_httpx_exceptions():
    """Raw HTTP client exceptions must never propagate past the provider boundary."""
    provider = OpenRouterProvider(_settings())
    with (
        patch(
            "app.ai.providers.openrouter.httpx.post",
            side_effect=httpx.ReadTimeout("read timeout"),
        ),
        pytest.raises(AIProviderException),
    ):
        try:
            provider.generate(Prompt(system="sys", user="usr"))
        except httpx.HTTPError:
            pytest.fail("httpx exception leaked past the provider boundary")
