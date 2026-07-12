import logging

import httpx

from app.ai.provider import AIProviderInterface, AIProviderResponse, Prompt
from app.core.config import Settings
from app.core.exceptions import AIProviderConfigurationException, AIProviderException

logger = logging.getLogger(__name__)

PROVIDER_NAME = "openrouter"


class OpenRouterProvider(AIProviderInterface):
    """AI provider adapter for OpenRouter's OpenAI-compatible Chat Completions API.

    All OpenRouter-specific concerns (endpoint, authentication header,
    request/response shape) are isolated here. No other component may
    depend on this class.
    """

    def __init__(self, settings: Settings):
        if not settings.openrouter_api_key:
            raise AIProviderConfigurationException(
                "OpenRouter is not properly configured: missing API key."
            )
        self._api_key = settings.openrouter_api_key
        self._base_url = settings.openrouter_base_url.rstrip("/")
        self._model = settings.openrouter_model
        self._timeout = settings.ai_request_timeout_seconds
        self._max_tokens = settings.ai_max_tokens

    def generate(self, prompt: Prompt) -> AIProviderResponse:
        try:
            response = httpx.post(
                f"{self._base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": prompt.system},
                        {"role": "user", "content": prompt.user},
                    ],
                    "max_tokens": self._max_tokens,
                },
                timeout=self._timeout,
            )
        except httpx.TimeoutException as exc:
            logger.error(
                "OpenRouter request timed out",
                extra={"provider": PROVIDER_NAME, "model": self._model},
            )
            raise AIProviderException("AI provider request timed out.") from exc
        except httpx.RequestError as exc:
            logger.error(
                "OpenRouter request failed",
                extra={"provider": PROVIDER_NAME, "model": self._model},
            )
            raise AIProviderException("Failed to reach the AI provider.") from exc

        if response.status_code >= 400:
            logger.error(
                "OpenRouter returned a non-success response",
                extra={
                    "provider": PROVIDER_NAME,
                    "model": self._model,
                    "status_code": response.status_code,
                },
            )
            raise AIProviderException(
                f"AI provider returned an error status: {response.status_code}."
            )

        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            logger.error(
                "OpenRouter returned a malformed response",
                extra={"provider": PROVIDER_NAME, "model": self._model},
            )
            raise AIProviderException(
                "AI provider returned a malformed response."
            ) from exc

        if not content or not content.strip():
            raise AIProviderException("AI provider returned an empty response.")

        return AIProviderResponse(
            content=content, provider=PROVIDER_NAME, model=self._model
        )
