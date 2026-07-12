"""AI Provider Manager: resolves the configured provider and routes requests to it.

Business logic (the AI Service) depends only on this manager and the
provider-neutral types in app.ai.provider — never on a concrete provider
implementation.
"""

from app.ai.provider import AIProviderInterface, AIProviderResponse, Prompt
from app.ai.providers.openrouter import OpenRouterProvider
from app.core.config import Settings, get_settings
from app.core.exceptions import UnsupportedProviderException

# Registry of supported providers and the settings field naming their model.
# Adding a future provider requires only a new entry here and a new adapter
# under app/ai/providers/ — no change to business logic.
_PROVIDER_REGISTRY: dict[str, type[AIProviderInterface]] = {
    "openrouter": OpenRouterProvider,
}
_PROVIDER_MODEL_SETTING: dict[str, str] = {
    "openrouter": "openrouter_model",
}


class AIManager:
    """Resolves the configured AI provider and executes generation requests."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    @staticmethod
    def supported_providers() -> list[str]:
        """Return the names of all currently implemented AI providers."""
        return sorted(_PROVIDER_REGISTRY.keys())

    def resolve_provider_name(self) -> str:
        """Return the configured provider name, validating it is supported."""
        provider_name = self.settings.ai_provider
        if provider_name not in _PROVIDER_REGISTRY:
            raise UnsupportedProviderException(
                f"Unsupported AI provider configured: '{provider_name}'."
            )
        return provider_name

    def resolve_model_name(self) -> str:
        """Return the configured model name for the active provider."""
        provider_name = self.resolve_provider_name()
        setting_name = _PROVIDER_MODEL_SETTING[provider_name]
        return getattr(self.settings, setting_name)

    def generate(self, prompt: Prompt) -> AIProviderResponse:
        """Invoke the configured provider and return its provider-neutral result."""
        provider_name = self.resolve_provider_name()
        provider_cls = _PROVIDER_REGISTRY[provider_name]
        provider = provider_cls(self.settings)
        return provider.generate(prompt)
