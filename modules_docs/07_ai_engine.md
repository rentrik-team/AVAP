# AI Engine Module

**Module:** 07 - AI Engine

**File:** `modules_docs/07_ai_engine.md`

**Version:** 1.0

**Status:** Planned

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

The AI Engine owns recommendation records.

Typical fields:

* Recommendation ID
* Vulnerability ID
* Risk Assessment ID
* Provider
* Model
* Prompt Version
* Recommendation
* Generated At

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

Current endpoints:

```text id="4s07dn"
GET /ai/recommendations/{assessment_id}

GET /ai/providers

GET /ai/models
```

Future endpoints:

```text id="jlwmdd"
POST /ai/regenerate

POST /ai/provider/test

GET /ai/history
```

---

# Testing Requirements

## Unit Tests

* Prompt Builder
* Prompt Validator
* Provider Manager
* Response Validator
* Recommendation Processor

---

## Integration Tests

* OpenRouter integration
* Provider abstraction
* Response validation
* Recommendation persistence
* Failure handling

---

## Security Tests

* Prompt injection attempts
* Malformed responses
* Missing API keys
* Provider failures
* Invalid model selection

---

# Definition of Done

The AI Engine module is complete only when:

* Provider abstraction implemented
* Prompt Builder implemented
* Prompt Validator implemented
* Provider Manager implemented
* OpenRouter provider implemented
* Response Validator implemented
* Recommendation Processor implemented
* Recommendation persistence completed
* REST APIs completed
* Unit tests passing
* Integration tests passing
* Security tests completed
* Documentation updated
* Git commit created according to project standards

Only after meeting all criteria may development proceed to the Reporting Engine module.

---

# Related Documentation

* `modules_docs/06_risk_assessment.md`
* `architecture_docs/system_architecture.md`
* `architecture_docs/data_flow.md`
* `architecture_docs/security.md`
* `architecture_docs/development_standards.md`
* `backend/backend.md`
