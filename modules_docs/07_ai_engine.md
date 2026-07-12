# AI Engine Module

**Module:** 07 - AI Engine

**File:** `modules_docs/07_ai_engine.md`

**Version:** 1.0

**Status:** Implemented

---

# Purpose

The AI Engine is responsible for providing intelligent, contextual, and explainable remediation guidance based on deterministic risk assessments produced by the Risk Assessment module.

The AI Engine serves as an **advisory layer** within the platform. It enriches vulnerability findings by generating human-readable explanations, remediation recommendations, prioritization guidance, and executive summaries.

The AI Engine **never performs security analysis independently** and **never overrides deterministic calculations** performed by the Risk Assessment module.

---

# Objectives

The AI Engine is designed to:

* Generate remediation recommendations
* Explain vulnerabilities in natural language
* Prioritize remediation efforts
* Produce executive summaries
* Assist report generation
* Abstract AI providers
* Support multiple LLM providers
* Prevent vendor lock-in

---

# Responsibilities

The AI Engine is responsible for:

* Receiving deterministic Risk Assessments
* Building AI prompts
* Communicating with configured AI providers
* Processing AI responses
* Validating generated recommendations
* Storing AI recommendations
* Supplying recommendations to the Reporting Engine

The AI Engine is **not responsible for**:

* Executing scanners
* Parsing scanner output
* Calculating risk
* Modifying vulnerabilities
* Updating database entities outside its own recommendations
* Making autonomous security decisions

---

# Design Principles

The AI Engine follows:

* AI as Advisory Only
* Provider Independence
* Deterministic Business Logic
* Prompt Isolation
* Explainability
* Secure AI Communication
* Fail Gracefully
* Loose Coupling

The platform must remain fully functional even if AI services are unavailable.

---

# High-Level Architecture

```text id="g0c8mh"
              Risk Assessment
                     │
                     ▼
           Recommendation Request
                     │
                     ▼
             Prompt Builder
                     │
                     ▼
            Prompt Validator
                     │
                     ▼
            AI Provider Manager
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
   OpenRouter      Groq         Gemini
       │             │             │
       └─────────────┼─────────────┘
                     ▼
            Response Validator
                     │
                     ▼
      Recommendation Processor
                     │
                     ▼
        AI Recommendation Model
                     │
                     ▼
            Reporting Engine
```

---

# Internal Components

| Component                 | Responsibility                                 |
| ------------------------- | ---------------------------------------------- |
| AI Coordinator            | Entry point of the AI Engine                   |
| Prompt Builder            | Creates structured prompts                     |
| Prompt Validator          | Validates prompts before sending               |
| Provider Manager          | Manages AI provider selection                  |
| Provider Interface        | Common interface implemented by every provider |
| Response Validator        | Validates AI responses                         |
| Recommendation Processor  | Converts responses into platform models        |
| Recommendation Repository | Stores AI recommendations                      |

---

# Implemented Architecture

The conceptual components above map onto the following concrete modules
(`backend/app/ai/`). Two components are intentionally consolidated rather
than implemented as separate near-empty files, since their responsibility
is already fully satisfied elsewhere:

| Conceptual Component | Implementation |
|---|---|
| AI Coordinator | `app/services/ai_service.py` (`AIService`) — the actual orchestration entry point |
| Prompt Builder | `app/ai/prompt_builder.py` |
| Prompt Validator | Folded into `AIRemediationContext`'s Pydantic field bounds (`app/schemas/ai.py`); a context that fails validation never reaches the prompt builder |
| Provider Manager | `app/ai/manager.py` (`AIManager`) |
| Provider Interface | `app/ai/provider.py` (`AIProviderInterface`, `Prompt`, `AIProviderResponse`) |
| OpenRouter Provider | `app/ai/providers/openrouter.py` |
| Response Validator | `app/ai/response_validator.py` |
| Recommendation Processor | Folded into `response_validator.py` (parses/validates) and `AIService` (persists); no separate processor module |
| Recommendation Repository | `app/repositories/ai_recommendation_repository.py` |
| AI Recommendation Model | `app/models/ai_recommendation.py` |

---

# Processing Workflow

```text id="xytqij"
Risk Assessment

↓

Recommendation Request

↓

Prompt Builder

↓

Prompt Validation

↓

Provider Selection

↓

AI Request

↓

Response Validation

↓

Recommendation Processing

↓

Recommendation Storage

↓

Reporting Engine
```

The AI Engine never receives scanner output directly.

---

# AI Provider Architecture

The platform follows a provider abstraction model.

```text id="oq8t7t"
Business Logic

↓

Provider Interface

↓

Provider Manager

↓

OpenRouter

↓

Model
```

Future providers:

* Groq
* Google Gemini
* Hugging Face
* Azure OpenAI
* AWS Bedrock

Switching providers should require changes only inside provider implementations.

---

# Supported AI Providers

Primary provider:

* OpenRouter

Future supported providers:

* Groq
* Google Gemini
* Hugging Face

The AI Engine must never depend directly on provider SDKs outside the Provider Layer.

---

# Prompt Builder

The Prompt Builder constructs structured prompts using:

* Asset information
* Vulnerability information
* Risk Assessment
* Scanner metadata
* Contextual information

Prompt templates should remain version-controlled.

Prompt generation must be deterministic.

---

# Prompt Validation

Every prompt is validated before transmission.

Validation includes:

* Required fields
* Token estimation
* Input sanitization
* Prompt size limits
* Context verification

Sensitive information should be excluded whenever possible.

---

# Provider Manager

The Provider Manager is responsible for:

* Selecting configured provider
* Routing requests
* Handling provider failures
* Managing retries (future)
* Applying provider configuration

Business logic must remain unaware of provider implementation details.

---

# Provider Interface

Every AI provider must implement a common interface.

Responsibilities include:

* Authentication
* Request execution
* Response handling
* Error reporting

All providers return a standardized internal response model.

---

# Response Validation

AI responses are treated as untrusted input.

Validation includes:

* Response structure
* Required sections
* Maximum response length
* Content safety checks
* Empty response detection

Invalid responses are rejected.

---

# Recommendation Processing

Validated AI responses are converted into structured recommendations.

Typical outputs include:

* Vulnerability explanation
* Business impact summary
* Remediation steps
* Mitigation guidance
* Best practices
* References

Recommendations are stored independently of deterministic risk records.

---

# AI Recommendation Model

The AI Engine owns recommendation records, persisted in `ai_recommendations`.

Implemented fields:

* Recommendation ID (`id`)
* Vulnerability ID (`vulnerability_id`, FK, denormalized from the risk assessment for efficient lookup)
* Risk Assessment ID (`risk_assessment_id`, FK — must reference a `VULNERABILITY`-scope `RiskAssessment`; enforced by the service layer, since a CHECK constraint cannot portably validate another table's column)
* Provider (`provider`)
* Model (`model`)
* Prompt Version (`prompt_version`)
* Recommendation, split into its structured parts: `summary`, `explanation`, `remediation_steps`, `validation_steps`, `cautions` (JSONB list columns for the three step collections)
* Generated At (`generated_at`)

A unique constraint on `(risk_assessment_id, provider, model, prompt_version)`
defines recommendation identity (see Recommendation Identity below).

Deliberately not persisted: API keys, authorization headers, full provider
HTTP responses, or chain-of-thought/hidden reasoning. Only the final
structured recommendation is stored.

Future fields:

* Confidence Score
* Response Metadata
* Token Usage

---

# Data Flow

```text id="7bg3kt"
Risk Assessment

↓

AI Engine

↓

Recommendation

↓

Reporting Engine
```

Only deterministic risk data enters the AI Engine.

---

# Recommendation Identity and Regeneration

A recommendation's identity is the tuple `(risk_assessment_id, provider,
model, prompt_version)`. This is enforced by a database unique constraint,
not by application-level SELECT-then-INSERT logic.

Behavior:

* **First generation** — inserts a new recommendation row.
* **Repeated generation, unchanged risk assessment** — the existing
  recommendation is returned without calling the AI provider again
  (`recommendation.generated_at >= risk_assessment.calculated_at`).
  Regeneration is intentional, not silently cached: calling
  `POST /ai/recommendations/{assessment_id}/generate` is always safe, but
  only issues a fresh provider call when there is a genuine reason to.
* **Risk assessment recalculated since the last recommendation** —
  the provider is called again and the existing row is updated in place
  (same identity, refreshed content and `generated_at`).
* **Changed prompt version, model, or provider** — a new identity
  combination, so a new recommendation row is created; prior recommendations
  for the previous configuration remain available for audit/comparison.
* **Provider failure or invalid AI output** — the exception propagates
  and nothing is persisted; any previously valid recommendation for that
  identity is left untouched.
* **Persistence failure** — the transaction is rolled back; no partial
  recommendation is ever stored.

---

# Prompt Security Boundary (Implemented)

Every prompt has two parts: a stable system message (AVAP's role, the
advisory-only constraint, and the required JSON output schema) and a user
message containing the task instruction followed by the serialized
`AIRemediationContext` inside explicit `<<<BEGIN/END ASSESSMENT DATA>>>`
markers, with a closing reminder that content inside those markers is data,
never instructions. Untrusted vulnerability/service/product text can never
leave the data section or influence the system instructions, because the
system message is a fixed string independent of the request.

---

# AI Constraints

The AI Engine must never:

* Modify Risk Scores
* Modify Severity
* Modify Vulnerability Records
* Change Asset Information
* Execute Commands
* Access Database Directly
* Execute Shell Commands
* Make Autonomous Decisions

The AI Engine provides recommendations only.

---

# Failure Handling

The platform must remain operational when AI services fail.

Failure scenarios include:

* Provider unavailable
* Network timeout
* Rate limiting
* Invalid response
* Authentication failure
* Token exhaustion

In failure scenarios:

* Risk Assessment remains available.
* Reports continue to generate.
* AI sections may indicate recommendations are unavailable.

---

# Security Requirements

The AI Engine shall:

* Validate every request
* Validate every response
* Sanitize prompts
* Sanitize responses
* Protect API keys
* Prevent prompt injection where practical
* Limit provider permissions
* Log failures without exposing secrets

The AI Engine must never expose:

* Environment variables
* Internal architecture
* Database credentials
* API keys

---

# Logging

The AI Engine should log:

* Provider selected
* Model used
* Request initiated
* Response received
* Validation failures
* Provider failures
* Processing duration

Logs should include:

* Scan ID
* Assessment ID
* Provider
* Model
* Processing Time

Prompt contents should not be logged in production.

---

# Dependencies

Depends on:

* Risk Assessment Module
* Configuration Module
* Logging Module

Communicates with:

* Reporting Engine

Does not communicate with:

* Scanner Engine
* Parser Engine
* Asset Management

---

# Performance Considerations

The AI Engine should:

* Reuse prompt templates
* Minimize token usage
* Cache reusable static prompt sections
* Support configurable models
* Avoid duplicate requests

Future implementations may introduce response caching for identical recommendation requests.

---

# Future Enhancements

The architecture supports:

* Multiple model selection
* Provider fallback
* Automatic retries
* Streaming responses
* Prompt versioning
* Local model integration (optional)
* Organization-specific prompt templates
* Multi-language recommendations
* Compliance-specific remediation
* Threat intelligence augmentation
* Cost-aware provider routing

These enhancements should integrate without changing the Provider Interface.

---

# REST APIs

Base endpoint:

```text id="uvry1u"
/api/v1/ai
```

Implemented endpoints:

```text id="4s07dn"
GET /ai/recommendations/{assessment_id}

POST /ai/recommendations/{assessment_id}/generate

GET /ai/providers

GET /ai/models
```

`{assessment_id}` is the ID of a `VULNERABILITY`-scope `RiskAssessment`
record (Module 06). `GET` never triggers generation (404 if none exists
yet); `POST .../generate` is the minimum necessary trigger endpoint — the
same disciplined addition made for Module 06's `/risk/scans/{id}/calculate`,
since the documented "current" endpoints alone provide no way to ever
produce a recommendation. It is idempotent per the identity rules above.

`GET /ai/providers` returns the supported provider registry and the
currently configured active provider. `GET /ai/models` returns the model
configured for the active provider. Neither makes a network call or
requires the AI provider's API key to be set.

Future endpoints:

```text id="jlwmdd"
POST /ai/regenerate

POST /ai/provider/test

GET /ai/history
```

---

# Testing Requirements

Implemented in `backend/tests/ai/`, `backend/tests/repositories/test_ai_recommendation_repository.py`,
`backend/tests/services/test_ai_service.py`, `backend/tests/services/test_ai_integration.py`,
and `backend/tests/api/test_ai_api.py` (80 tests total).

## Unit Tests

* Prompt Builder: deterministic construction, required system instructions,
  data trust boundary, output contract instructions, prompt-injection
  containment, `None` field exclusion
* Provider Manager: provider resolution, unsupported provider, model
  resolution, configuration-error propagation
* OpenRouter Provider: success extraction, timeout, network failure,
  non-success status, malformed response, empty response, authorization
  header construction, no HTTP client exception leakage
* Response Validator: valid/malformed/empty responses, missing fields,
  wrong types, blank/oversized step collections, markdown code-fence
  normalization, arbitrary text rejection, no eval of AI output

---

## Integration Tests

* Module 05 findings → Module 06 risk calculation → Module 07 remediation
  context → fake provider (at the provider interface boundary) → validated
  recommendation → persistence → AI API retrieval, with Module 06 risk
  fields verified unchanged throughout
* Repository idempotency and uniqueness against a real database session
* Service-level failure handling (provider failure, invalid output,
  transaction rollback, prior recommendation preserved)

---

## Security Tests

* Prompt injection in vulnerability description and service/product metadata
* Provider endpoint/provider selection cannot be influenced by request body
* API keys and authorization headers never appear in error responses
* Provider raw error payloads never appear in error responses
* Invalid AI output cannot reach persistence
* The structured output contract has no field capable of expressing risk;
  generating a recommendation never modifies the referenced `RiskAssessment`

---

# Definition of Done

The AI Engine module is complete only when:

* [x] Provider abstraction implemented (`app/ai/provider.py`, `app/ai/manager.py`)
* [x] Prompt Builder implemented (`app/ai/prompt_builder.py`)
* [x] Prompt Validator implemented (via `AIRemediationContext` field bounds)
* [x] Provider Manager implemented (`AIManager`)
* [x] OpenRouter provider implemented (`app/ai/providers/openrouter.py`)
* [x] Response Validator implemented (`app/ai/response_validator.py`)
* [x] Recommendation Processor implemented (validator + `AIService`)
* [x] Recommendation persistence completed (`ai_recommendations` table, migration `0005`)
* [x] REST APIs completed (`/api/v1/ai/*`)
* [x] Unit tests passing
* [x] Integration tests passing
* [x] Security tests completed
* [x] Documentation updated
* [x] Git commit created according to project standards

Only after meeting all criteria may development proceed to the Reporting Engine module.

---

# Related Documentation

* `modules_docs/06_risk_assessment.md`
* `architecture_docs/system_architecture.md`
* `architecture_docs/data_flow.md`
* `architecture_docs/security.md`
* `architecture_docs/development_standards.md`
* `backend/backend.md`
