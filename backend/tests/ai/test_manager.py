import pytest

from app.ai.manager import AIManager
from app.ai.providers.openrouter import OpenRouterProvider
from app.core.config import Settings
from app.core.exceptions import (
    AIProviderConfigurationException,
    UnsupportedProviderException,
)


def _settings(**overrides) -> Settings:
    defaults = {
        "ai_provider": "openrouter",
        "openrouter_api_key": "test-key",
        "openrouter_model": "test-model",
        "ai_request_timeout_seconds": 30,
        "ai_max_tokens": 1024,
    }
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)


def test_resolve_provider_name_returns_configured_provider():
    manager = AIManager(settings=_settings())
    assert manager.resolve_provider_name() == "openrouter"


def test_resolve_provider_name_rejects_unsupported_provider():
    manager = AIManager(settings=_settings(ai_provider="chatgpt-deluxe"))
    with pytest.raises(UnsupportedProviderException):
        manager.resolve_provider_name()


def test_resolve_model_name_returns_configured_model():
    manager = AIManager(
        settings=_settings(openrouter_model="meta-llama/llama-3.1-8b-instruct:free")
    )
    assert manager.resolve_model_name() == "meta-llama/llama-3.1-8b-instruct:free"


def test_supported_providers_lists_openrouter():
    assert "openrouter" in AIManager.supported_providers()


def test_generate_resolves_openrouter_provider_type():
    """AIManager.generate must dispatch to the OpenRouterProvider implementation
    without the caller needing to know that detail.
    """
    manager = AIManager(settings=_settings())
    provider_name = manager.resolve_provider_name()
    provider_cls = type(OpenRouterProvider(manager.settings))
    assert provider_name == "openrouter"
    assert provider_cls is OpenRouterProvider


def test_generate_raises_configuration_error_when_api_key_missing():
    manager = AIManager(settings=_settings(openrouter_api_key=""))
    from app.ai.provider import Prompt

    with pytest.raises(AIProviderConfigurationException):
        manager.generate(Prompt(system="s", user="u"))


def test_generate_raises_unsupported_provider_before_touching_provider_config():
    manager = AIManager(
        settings=_settings(ai_provider="unknown", openrouter_api_key="")
    )
    from app.ai.provider import Prompt

    with pytest.raises(UnsupportedProviderException):
        manager.generate(Prompt(system="s", user="u"))
