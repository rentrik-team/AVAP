# Backend Development Guide

**File:** `backend/backend.md`

**Version:** 1.0

**Status:** Active

---

# Purpose

This document defines the backend implementation guidelines for the Automated Vulnerability Assessment Platform (AVAP).

It serves as the primary reference for backend development and complements:

- ai_contract.md
- architecture_docs/system_architecture.md
- architecture_docs/development_standards.md
- architecture_docs/database.md
- architecture_docs/security.md

Implementation should always follow these documents.

---

# Backend Technology Stack

| Component | Technology |
|------------|------------|
| Language | Python 3.12+ |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x |
| Validation | Pydantic v2 |
| Database | PostgreSQL |
| Migration | Alembic |
| Testing | Pytest |
| PDF | ReportLab |
| Scanner | Nmap |
| Vulnerability Scanner | OpenVAS CE |

No technology should be replaced without architectural review.

---

# Backend Directory Structure

```
backend/

app/
│
├── api/
│
├── core/
│
├── database/
│
├── models/
│
├── schemas/
│
├── repositories/
│
├── services/
│
├── scanners/
│
├── parsers/
│
├── risk_engine/
│
├── ai/
│
├── reporting/
│
├── middleware/
│
├── exceptions/
│
├── dependencies/
│
├── utils/
│
└── main.py

tests/

scripts/

alembic/
```

Every package has a single responsibility.

---

# API Architecture

API routes are responsible only for:

- request validation
- dependency injection
- calling services
- returning responses

Routes must never:

- contain business logic
- communicate with database
- invoke scanners
- calculate risk
- generate reports

---

# Service Layer

The Service Layer owns:

- business rules
- workflow orchestration
- module coordination
- validation beyond request schemas

Only services may communicate with multiple components.

## Audit event transaction pattern (Module 10)

Services that append a security-relevant `AuditEvent` (`app/services/audit_service.py`)
follow one of two patterns depending on whether the service already owns an
explicit transaction:

- **Shared transaction (preferred):** `AuditService.append_event(...)` (add +
  flush only, never commit) is called *before* the service's own
  `session.commit()`. If the audit insert or its metadata validation fails,
  the exception propagates into the service's existing rollback path, so the
  business action is never reported as successful without its audit event.
  Used by `RiskService`, `AIService`, `ReportService`, `InventoryService`.
- **Best-effort, post-commit:** for repositories that already commit
  synchronously inside their own `create`/`update`/`delete` methods
  (`TargetRepository`, `ScanRepository` — a pre-Module-10 pattern not
  redesigned by this module), the audit event is appended and committed
  immediately after, in its own try/except. A failure here is logged and
  swallowed rather than raised, since the business mutation has already
  durably happened and cannot be rolled back at that point. Used by
  `TargetService`, `ScanService`.

A FAILURE audit event is always recorded via
`AuditService.record_failure_safely(...)`, in a fresh transaction *after*
the business rollback, and never raises itself — it logs and swallows so it
can never replace the real business exception with an audit-subsystem error.

Per-request actor/correlation context (`app/audit/context.py`) is resolved by
a FastAPI dependency (`app/api/dependencies/audit.py`) from the real ASGI
connection and a request-ID middleware
(`app/api/middleware/request_context.py`) — never from the full `Request`
object passed into a service, and never from a client-supplied header
claiming an actor identity.

---

# Repository Layer

Repositories own:

- CRUD
- database queries
- transactions
- persistence

Repositories never contain business logic.

---

# Database Access

Database access always follows:

```
API

↓

Service

↓

Repository

↓

SQLAlchemy

↓

PostgreSQL
```

No component may bypass repositories.

---

# Scanner Integration

Scanner execution is isolated.

```
Service

↓

Scanner Engine

↓

Scanner Adapter

↓

Nmap/OpenVAS
```

Scanner output must always pass through parser components.

---

# AI Integration

The AI engine communicates only through provider interfaces.

```
Service

↓

AI Interface

↓

Provider

↓

OpenRouter
```

Future providers:

- Groq
- Gemini
- HuggingFace

No business logic depends directly on a provider SDK.

---

# Configuration

All configuration originates from environment variables.

Configuration loading is centralized.

Never read environment variables directly inside business logic.

---

# Required Environment Variables

## Application

```text
APP_NAME

APP_VERSION

ENVIRONMENT

DEBUG

API_V1_PREFIX
```

---

## Database

```text
DATABASE_URL

POSTGRES_HOST

POSTGRES_PORT

POSTGRES_DB

POSTGRES_USER

POSTGRES_PASSWORD
```

---

## Scanner

```text
NMAP_EXECUTABLE

SCAN_TIMEOUT

OPENVAS_HOST

OPENVAS_PORT

OPENVAS_USERNAME

OPENVAS_PASSWORD
```

---

## AI

```text
AI_PROVIDER

AI_REQUEST_TIMEOUT_SECONDS

AI_MAX_TOKENS

OPENROUTER_API_KEY

OPENROUTER_BASE_URL

OPENROUTER_MODEL

GROQ_API_KEY

GEMINI_API_KEY

HUGGINGFACE_API_KEY
```

---

## Reports

```text
REPORT_OUTPUT_DIRECTORY
```

---

## Logging

```text
LOG_LEVEL

LOG_DIRECTORY
```

---

# Environment Files

The repository should contain:

```
.env.example
```

The following files should never be committed:

```
.env

.env.local

.env.production

.env.development
```

The application should fail during startup if required environment variables are missing.

---

# Repository Configuration

The repository shall contain a `.gitignore` configured for Python, FastAPI, PostgreSQL, and security-sensitive files.

Recommended exclusions include:

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo

# Virtual Environment
venv/
.venv/

# Environment Files
.env
.env.*
!.env.example

# IDE
.vscode/
.idea/

# Logs
logs/
*.log

# Reports
generated_reports/

# Scanner Output
scanner_output/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Build
dist/
build/

# Database
*.db
*.sqlite3

# Temporary
tmp/
temp/

# Security
*.pem
*.key
*.crt
*.pfx

# Python
.mypy_cache/
.ruff_cache/
```

---

# Git Workflow

Development follows a module-based workflow.

Every module must be completed independently.

A module is considered complete only after:

- implementation completed
- API completed
- tests passing
- documentation updated
- architecture reviewed
- repository clean

Only then may development continue.

---

# Commit Policy

Every completed module shall result in a Git commit.

The AI agent should commit only after verifying:

- no unused imports
- no commented code
- no dead code
- no TODO placeholders
- no debugging statements
- tests passing
- documentation updated
- project builds successfully

---

# Commit Message Convention

Use Conventional Commits.

Examples:

```
feat(target-validation): implement target validation module

feat(scanner-engine): integrate nmap adapter

feat(parser): add xml normalization

feat(reporting): implement pdf report generation

fix(risk-engine): correct severity calculation

refactor(repository): simplify query implementation

docs(database): update database architecture

test(scanner): add scanner integration tests

chore(dependencies): update project dependencies
```

Commits should represent one logical unit of work.

---

# AI Development Workflow

When implementing a feature, AI agents should follow this sequence:

1. Review relevant documentation.
2. Implement the feature.
3. Add or update unit tests.
4. Add or update integration tests.
5. Update affected documentation.
6. Verify architecture consistency.
7. Ensure repository cleanliness.
8. Create a Git commit.
9. Proceed to the next module only after the commit.

---

# Dependency Management

Prefer:

1. Python Standard Library
2. FastAPI
3. SQLAlchemy
4. Pydantic
5. PostgreSQL native features
6. Official SDKs
7. Mature open-source libraries

Custom implementations should be the final option.

Do not introduce dependencies for trivial functionality.

---

# Backend Security

Backend code must:

- validate all inputs
- use parameterized queries
- avoid shell=True
- avoid hardcoded credentials
- avoid dynamic SQL
- sanitize external inputs
- use structured logging

Sensitive information must never appear in:

- logs
- exceptions
- responses
- commits

---

# Testing

Every backend module requires:

- unit tests
- integration tests
- API tests

Tests should mirror the application structure.

---

# Logging

Use structured logging.

Every log should contain:

- timestamp
- module
- severity
- operation
- message

Future versions should include request correlation IDs.

---

# Error Handling

Errors should propagate through centralized exception handlers.

Internal exceptions must never leak implementation details.

Unexpected failures should be logged.

Client responses should remain sanitized.

---

# Backend Definition of Done

Backend work is considered complete only when:

- implementation complete
- tests passing
- documentation updated
- architecture maintained
- security validated
- repository clean
- Git commit created

Only then should the next module begin.

---

# Related Documentation

- `ai_contract.md`
- `project.md`
- `architecture_docs/system_architecture.md`
- `architecture_docs/data_flow.md`
- `architecture_docs/database.md`
- `architecture_docs/security.md`
- `architecture_docs/development_standards.md`
- `modules_docs/`


# Pre-Commit Quality Gate

Before creating a Git commit, the AI agent shall verify:

- Project runs successfully.
- All tests pass.
- No linting errors (Ruff/Flake8 if configured).
- Code formatting is applied (Black).
- Import ordering is correct (isort).
- No secrets or credentials are present.
- No temporary or debug code remains.
- Documentation reflects the implementation.
- New environment variables are added to `.env.example`.
- `.gitignore` covers any newly generated files.
- Commit message follows Conventional Commits.

If any check fails, the issue must be resolved before committing.