
# Purpose

This document is the primary contract that governs every AI agent contributing to the Automated Vulnerability Assessment Platform (AVAP).

It defines mandatory engineering principles, architectural constraints, development workflow, coding standards, documentation rules, and security requirements.

Every generated artifact—including documentation, architecture decisions, source code, database schemas, tests, APIs, and future enhancements—must comply with this contract.

If any future instruction conflicts with this document, this contract takes precedence unless the project owner explicitly overrides it.

---

# Project Identity

**Project Name**

Automated Vulnerability Assessment Platform (AVAP)

**Project Type**

Enterprise-grade cybersecurity platform.

**Project Objective**

Develop a production-ready vulnerability assessment platform using entirely free and open-source technologies.

The platform must follow industry-grade architecture comparable to commercial products such as Tenable, Qualys, and Rapid7 from an engineering perspective (not feature parity).

This is **not** a demonstration, tutorial, proof of concept, or academic project.

Every implementation decision shall assume long-term maintainability, extensibility, and enterprise deployment.

---

# Project Vision

The platform shall provide an automated security assessment pipeline:

Asset Discovery

↓

Port & Service Enumeration

↓

Vulnerability Assessment

↓

Risk Analysis

↓

AI-assisted Remediation

↓

Professional Report Generation

Future phases may include:

* Scheduled scanning
* Distributed scanners
* Multi-user support
* Authentication
* RBAC
* Notifications
* Compliance reporting
* Dashboards
* Integrations
* Plugin ecosystem
* Multi-tenant architecture

Current implementation must never prevent these future capabilities.

---

# Current Development Phase

Current focus:

**Full-Stack Refinement** — the backend and the Next.js frontend are both
built and shipped (frontend delivered across commits aaedddb→629bff5);
ongoing work refines and hardens the existing stack.

The following are intentionally postponed:

* Authentication
* Authorization
* RBAC
* Multi-user support
* Distributed deployment
* CI/CD pipelines

Backend APIs shall be validated using Postman.

**Dockerization was delivered on owner request (2026-07-20).** A single-host
Docker Compose stack (PostgreSQL + backend + frontend) lives at the repo
root; see `deployment.md`. This is a single-machine deployment aid only — it
does not introduce distributed/orchestrated deployment, which remains
postponed.

---

# Core Engineering Philosophy

Every engineering decision shall prioritize:

1. Security
2. Architecture consistency
3. Maintainability
4. Extensibility
5. Readability
6. Reliability
7. Scalability
8. Performance
9. Developer experience

Development speed is never the primary decision factor.

---

# Project Architecture Principles

The system shall follow strict layered architecture.

```
Client (Future)

↓

REST API Layer

↓

Service Layer

↓

Repository Layer

↓

Database

Scanner Layer

↓

Parser Layer

↓

Risk Engine

↓

AI Engine

↓

Reporting Engine
```

Mandatory rules:

* Layers shall communicate only with adjacent layers.
* API routes shall never contain business logic.
* Services own business logic.
* Repositories own persistence.
* Database access shall never bypass repositories.
* External tools shall only be accessed through dedicated adapters.
* Business logic shall never directly invoke infrastructure implementations.

---

# Modular Architecture

The project shall remain modular.

Each module must have a clearly defined responsibility.

Modules must communicate using well-defined interfaces.

Modules shall avoid hidden dependencies.

Future modules must integrate without modifying existing business logic whenever possible.

---

# Dependency Direction

Dependencies shall always point inward.

```
Routes
↓

Services
↓

Repositories
↓

Database
```

Infrastructure components shall never dictate business rules.

Business logic shall remain independent of implementation details.

---

# Technology Stack

## Backend

* Python 3.12+
* FastAPI
* SQLAlchemy 2.x
* Alembic
* PostgreSQL
* Pydantic v2
* ReportLab
* Pytest

## Security Tools

* Nmap
* OpenVAS Community Edition

## Frontend (built)

* Next.js
* React
* TypeScript
* TailwindCSS

## Future Containerization

* Docker
* Docker Compose

Technology changes require explicit approval.

---

# AI Architecture Contract

The platform shall never depend directly on a single AI provider.

All AI interactions shall pass through an abstraction layer.

Supported providers include:

* OpenRouter (primary)
* Groq
* Google Gemini
* Hugging Face

Provider implementations shall be interchangeable.

Changing providers must require changes only within the provider implementation.

Business logic shall remain provider-agnostic.

Ollama shall not be considered the default deployment strategy.

---

# Development Workflow

Only one module shall be developed at a time.

A module is considered complete only after:

* implementation
* API
* validation
* unit tests
* integration tests (where applicable)
* documentation
* architecture review

No subsequent module shall begin before the previous module reaches completion.

---

# Documentation Contract

Project documentation shall remain structured.

```
project.md

ai_contract.md

architecture_docs/

backend/

frontend/

modules_docs/
```

Every document shall have a single responsibility.

Documentation shall avoid duplication.

Architecture decisions belong in architecture documentation.

Module implementation belongs in module documentation.

API documentation belongs in backend documentation.

---

# Coding Standards

Generated code shall follow:

* SOLID
* DRY
* KISS
* Clean Architecture
* Dependency Injection
* Composition over inheritance
* Explicit typing

Mandatory requirements:

* Type hints
* Small functions
* Small classes
* Clear naming
* Structured logging
* Meaningful exceptions
* Reusable utilities

Avoid:

* Large classes
* Circular dependencies
* Hidden side effects
* Global mutable state
* Tight coupling
* Premature optimization

---

# Security Contract

Security is the highest priority.

Every input shall be treated as hostile.

Every external interaction shall be validated.

The platform shall actively prevent:

* Command Injection
* SQL Injection
* Path Traversal
* SSRF
* XSS
* CSRF
* Remote Code Execution
* Unsafe deserialization
* Arbitrary file access

Mandatory secure coding rules:

* Never use `shell=True`
* Never concatenate shell commands
* Never trust user input
* Never expose secrets
* Never hardcode credentials
* Never store secrets in source code
* Validate all inputs
* Escape outputs where appropriate
* Use parameterized database queries
* Use environment variables for configuration

Development shall align with OWASP Secure Coding Practices.

---

# Database Contract

Database engine:

PostgreSQL

ORM:

SQLAlchemy

Migration:

Alembic

Rules:

* normalized schema
* foreign keys
* indexes
* constraints
* transactions
* repository ownership
* no SQL inside business logic

Database access shall always occur through repositories.

---

# REST API Contract

APIs shall follow REST principles.

Requirements:

* version-ready endpoints
* resource-oriented design
* request validation
* response validation
* consistent response schema
* proper HTTP status codes
* predictable error handling

Every endpoint shall be independently testable using Postman.

---

# Scanner Contract

Scanner integrations shall remain isolated.

Each scanner shall have its own adapter.

Business logic shall never invoke command-line tools directly.

Scanner output shall always pass through dedicated parser components.

Scanner implementations shall remain replaceable.

---

# Parser Contract

Raw scanner output shall never be consumed directly by business logic.

Every parser shall:

* validate data
* normalize formats
* handle malformed output
* produce strongly typed models

Parsers shall never contain business rules.

---

# Risk Engine Contract

Risk calculation shall remain independent of scanners.

The engine shall operate on normalized vulnerability models.

Risk calculations shall be deterministic.

Future enhancements may include:

* CVSS scoring
* environmental scoring
* exploit maturity
* asset criticality
* business impact

The architecture shall allow these extensions without breaking existing APIs.

---

# AI Engine Contract

AI shall assist—not replace—security analysis.

Responsibilities include:

* remediation guidance
* vulnerability explanation
* prioritization assistance
* report enrichment

AI shall never become the source of truth.

Risk scoring shall remain deterministic and rule-based.

AI outputs shall be treated as advisory.

---

# Reporting Contract

Reports shall be generated from normalized assessment data.

Report generation shall remain independent of scanners.

Future report formats may include:

* PDF
* JSON
* HTML
* CSV

Adding report formats shall not require modifications to business logic.

---

# Error Handling

Errors shall be:

* structured
* logged
* actionable
* non-sensitive

Internal implementation details shall never be exposed through API responses.

Unexpected exceptions shall be logged with sufficient diagnostic context while returning sanitized client responses.

---

# Logging Contract

Logging shall use structured logging.

Logs shall include:

* timestamps
* severity
* request correlation identifiers (future)
* module name
* operation
* failure reason

Sensitive information shall never be logged.

---

# Configuration Contract

Configuration shall originate from environment variables.

Configuration shall remain centralized.

No configuration values shall be hardcoded.

Environment-specific behavior shall be configurable without modifying source code.

---

# Testing Contract

Every module shall include automated tests.

Testing categories include:

* Unit Tests
* Integration Tests
* API Tests

Future additions:

* Performance Tests
* Security Tests
* End-to-End Tests

Production code shall not be accepted without corresponding tests.

---

# Documentation Generation Rules

Generated documentation shall:

* target professional engineering teams
* remain concise
* avoid repetition
* avoid tutorial-style explanations
* accurately reflect implementation
* remain synchronized with architecture

---

# Code Generation Rules

Generated code shall be:

* production-ready
* secure
* testable
* maintainable
* modular
* strongly typed

AI agents shall never generate placeholder implementations unless explicitly requested.

All generated code shall compile and integrate with the existing architecture.

---

# Architectural Decision Process

When multiple implementation approaches exist, decisions shall be evaluated using the following priority order:

1. Security
2. Maintainability
3. Reliability
4. Community adoption
5. Extensibility
6. Performance
7. Developer experience

The simplest implementation shall not automatically be selected.

Production-grade engineering practices shall take precedence over convenience.

---

# Change Management

Architectural changes require explicit approval.

New modules shall not violate existing architectural boundaries.

Backward compatibility should be preserved whenever practical.

Breaking changes shall be documented with rationale and migration considerations.

---

# AI Agent Responsibilities

Every AI agent contributing to this project shall:

* Read this contract before producing any output.
* Preserve architectural consistency.
* Respect module boundaries.
* Follow secure coding practices.
* Avoid unnecessary complexity.
* Generate production-quality artifacts.
* Update relevant documentation when implementation changes.
* Maintain consistency with previously established project structure.

No AI agent shall assume authority to redesign established architecture without explicit instruction.

---

# Definition of Done

A feature or module is complete only when:

* Architecture reviewed
* Implementation complete
* Code follows project standards
* APIs completed
* Validation implemented
* Error handling completed
* Tests passing
* Documentation updated
* Successfully integrated with the existing system

Only after meeting all criteria may development proceed to the next module.

---

# Governing Principle

Every future engineering decision shall answer the following question:

> **"Does this decision improve the long-term security, maintainability, extensibility, and architectural consistency of the platform?"**

If the answer is **No**, the implementation shall be reconsidered.

This document serves as the foundational engineering contract for the Automated Vulnerability Assessment Platform and shall guide all future AI-assisted development throughout the project lifecycle.


## Version Control Policy

Every completed module shall be committed to the Git repository before development proceeds to the next module.

A module is considered commit-ready only after:

- Implementation completed
- Tests passing
- Documentation updated
- Architecture consistency verified
- Static analysis passed (if configured)

Commit messages should follow:

<module>: <short description>

Examples:

feat(target-validation): implement target validation module

feat(scanner-engine): integrate nmap adapter

feat(reporting): add pdf generation

fix(risk-engine): correct cvss calculation

docs(database): update schema documentation

Development should never proceed to the next module without creating a logical Git commit.

# Repository Hygiene

After completing any implementation, the AI agent shall verify:

- No unused imports
- No commented code
- No dead code
- No duplicate logic
- No TODO placeholders
- No debugging statements
- No print() statements
- Documentation updated
- Tests updated
- Project builds successfully

Only after these checks should the Git commit be created.
