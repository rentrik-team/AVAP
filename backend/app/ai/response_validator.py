"""Response Validator: answers "does this AI output satisfy AVAP's remediation
contract?" — a distinct concern from provider transport, which only answers
"did the provider return a provider-neutral textual result?"

Raw AI output is always treated as untrusted input. No eval, no dynamic
code execution, no heuristic parsing of arbitrary text: the only accepted
normalization is stripping a single, common markdown code-fence envelope
around an otherwise valid JSON object.
"""

import json
import logging
import re

from pydantic import ValidationError

from app.core.exceptions import InvalidAIResponseException
from app.schemas.ai import RecommendationOutput

logger = logging.getLogger(__name__)

# Matches a single leading/trailing markdown code fence, optionally tagged
# "json" (e.g. ```json\n{...}\n```). This is the only formatting envelope
# normalized; no other heuristic unwrapping is attempted.
_CODE_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```$", re.DOTALL)


def _strip_code_fence(text: str) -> str:
    match = _CODE_FENCE_PATTERN.match(text.strip())
    return match.group(1).strip() if match else text.strip()


def validate_response(raw_content: str) -> RecommendationOutput:
    """Validate raw AI provider text against the structured remediation contract.

    Raises:
        InvalidAIResponseException: if the content is empty, is not valid
            JSON, or does not satisfy the RecommendationOutput contract.
    """
    if not raw_content or not raw_content.strip():
        raise InvalidAIResponseException("AI provider returned an empty response.")

    normalized = _strip_code_fence(raw_content)

    try:
        parsed = json.loads(normalized)
    except json.JSONDecodeError:
        logger.warning("AI response was not valid JSON")
        raise InvalidAIResponseException("AI response is not valid JSON.") from None

    try:
        return RecommendationOutput.model_validate(parsed)
    except ValidationError as exc:
        logger.warning(
            "AI response failed remediation contract validation",
            extra={"error_count": exc.error_count()},
        )
        raise InvalidAIResponseException(
            "AI response did not satisfy the required remediation contract."
        ) from None
