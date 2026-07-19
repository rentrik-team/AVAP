import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import RiskLevel

# Maximum characters of vulnerability description forwarded to the AI
# provider. Bounds prompt size and limits how much untrusted upstream
# scanner text is ever transmitted (data minimization).
MAX_DESCRIPTION_LENGTH = 2000


class AIRemediationContext(BaseModel):
    """Provider-neutral, validated remediation context for one vulnerability.

    Built exclusively from already-persisted Module 05/06 data. Never
    constructed from raw scanner output, and never serializes SQLAlchemy
    models directly.
    """

    vulnerability_id: uuid.UUID
    vulnerability_name: str = Field(..., max_length=200)
    cve: str | None = Field(None, max_length=20)
    description: str | None = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    severity_rating: str = Field(..., max_length=20)
    severity_score: float = Field(..., ge=0.0, le=10.0)
    risk_score: float = Field(..., ge=0.0, le=10.0)
    risk_level: RiskLevel
    calculation_version: str = Field(..., max_length=20)
    affected_service_name: str | None = Field(None, max_length=50)
    affected_product: str | None = Field(None, max_length=100)
    affected_version: str | None = Field(None, max_length=50)

    model_config = ConfigDict(frozen=True)


class RecommendationOutput(BaseModel):
    """Strict, provider-neutral structured remediation output contract.

    Every AI provider response must be validated against this schema before
    it may be persisted or returned through the API. Bounded lengths guard
    against pathological or oversized model output becoming uncontrolled
    application data.
    """

    summary: str = Field(..., min_length=1, max_length=500)
    explanation: str = Field(..., min_length=1, max_length=4000)
    remediation_steps: list[str] = Field(..., min_length=1, max_length=20)
    validation_steps: list[str] = Field(default_factory=list, max_length=20)
    cautions: list[str] = Field(default_factory=list, max_length=20)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("remediation_steps", "validation_steps", "cautions")
    @classmethod
    def _reject_blank_steps(cls, steps: list[str]) -> list[str]:
        for step in steps:
            if not step or not step.strip():
                raise ValueError("Step values must not be blank.")
        return steps


class AIRecommendationResponse(BaseModel):
    """Response model for a persisted AI remediation recommendation."""

    id: uuid.UUID
    vulnerability_id: uuid.UUID
    risk_assessment_id: uuid.UUID
    provider: str
    model: str
    prompt_version: str
    summary: str
    explanation: str
    remediation_steps: list[str]
    validation_steps: list[str]
    cautions: list[str]
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIServiceBanner(BaseModel):
    """One discovered network service, as reported by Nmap — a banner/version
    string, not a confirmed vulnerability. Forwarded to the AI as read-only
    context for it to reason about, never executed or trusted as instructions.
    """

    port: int = Field(..., ge=1, le=65535)
    protocol: str = Field(..., max_length=10)
    service_name: str = Field(..., max_length=50)
    product: str | None = Field(None, max_length=100)
    version: str | None = Field(None, max_length=50)

    model_config = ConfigDict(frozen=True)


class AIHostInventoryContext(BaseModel):
    """One scanned host's discovered service inventory, for vulnerability inference."""

    ip: str = Field(..., max_length=45)
    hostname: str | None = Field(None, max_length=255)
    operating_system: str | None = Field(None, max_length=200)
    services: list[AIServiceBanner] = Field(default_factory=list, max_length=100)

    model_config = ConfigDict(frozen=True)


_ALLOWED_SEVERITY_RATINGS = {"None", "Low", "Medium", "High", "Critical"}


class InferredVulnerabilityItem(BaseModel):
    """One AI-inferred vulnerability finding for a specific host/port.

    Strict, bounded contract — the same discipline as RecommendationOutput:
    every AI response is untrusted input until it satisfies this schema.
    """

    host: str = Field(..., max_length=45)
    port: int = Field(..., ge=1, le=65535)
    protocol: str = Field(..., max_length=10)
    name: str = Field(..., min_length=1, max_length=200)
    cve: str | None = Field(None, max_length=20)
    severity_rating: str = Field(..., max_length=20)
    severity_score: float = Field(..., ge=0.0, le=10.0)
    description: str = Field(..., min_length=1, max_length=MAX_DESCRIPTION_LENGTH)

    model_config = ConfigDict(str_strip_whitespace=True)

    @field_validator("severity_rating")
    @classmethod
    def _validate_severity_rating(cls, val: str) -> str:
        title_val = val.strip().title()
        if title_val not in _ALLOWED_SEVERITY_RATINGS:
            raise ValueError(
                f"severity_rating must be one of {sorted(_ALLOWED_SEVERITY_RATINGS)}"
            )
        return title_val


class VulnerabilityInferenceOutput(BaseModel):
    """Strict, provider-neutral structured contract for AI vulnerability inference.

    Bounded to at most 100 findings per scan — matches the service-count
    bound on AIHostInventoryContext, guarding against pathological AI output
    becoming uncontrolled application data.
    """

    findings: list[InferredVulnerabilityItem] = Field(
        default_factory=list, max_length=100
    )

    model_config = ConfigDict(str_strip_whitespace=True)


class AIProviderListResponse(BaseModel):
    """Response model listing supported and active AI providers."""

    supported_providers: list[str]
    active_provider: str


class AIModelResponse(BaseModel):
    """Response model describing the currently configured AI model."""

    provider: str
    model: str
