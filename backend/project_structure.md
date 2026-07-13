# Backend Project Structure

**File:** `backend/project_structure.md`

**Version:** 1.0

**Status:** Active

---

# Purpose

This document defines the official backend directory structure for the Automated Vulnerability Assessment Platform (AVAP).

Its objective is to ensure that every contributor and AI agent follows a consistent project layout.

No files or directories should be introduced unless they align with this structure.

This document serves as the authoritative reference for backend organization.

---

# Design Principles

The backend structure follows:

- Modular Monolith
- Layered Architecture
- Domain Separation
- Feature Isolation
- Single Responsibility Principle
- Dependency Inversion
- Scalability
- Maintainability

The structure is intentionally designed to support future migration toward microservices if required.

---

# Top-Level Structure

```text
backend/
│
├── app/
├── tests/
├── scripts/
├── alembic/
├── requirements/
├── .env.example
├── pyproject.toml
└── README.md
```

---

# Application Structure

```text
app/

├── api/

├── core/

├── database/

├── models/

├── schemas/

├── repositories/

├── services/

├── scanners/

├── parsers/

├── risk_engine/

├── ai/

├── reporting/

├── dashboard/

├── audit/

├── utils/

└── main.py
```

---

# app/api

Contains REST API implementation.

Responsibilities

- Versioned APIs
- Dependency Injection
- Middleware
- Request validation
- Response models

Structure

```text
api/

dependencies/

middleware/

responses/

routes/

└── v1/
```

Routes must never contain business logic.

---

# app/core

Contains global application configuration.

Responsibilities

- Configuration
- Constants
- Enums
- Logging
- Exceptions
- Security
- Settings

Example

```text
core/

config.py

constants.py

logging.py

exceptions.py

security.py

enums.py
```

---

# app/database

Contains database configuration.

Responsibilities

- Engine creation
- Session management
- Base model
- Alembic integration

Example

```text
database/

base.py

session.py
```

Repositories own all database access.

---

# app/models

Contains SQLAlchemy ORM models.

One entity per file.

Example

```text
target.py

scan_job.py

asset.py

service.py

port.py

vulnerability.py

risk.py

report.py

audit_log.py
```

Models must not contain business logic.

---

# app/schemas

Contains Pydantic request and response models.

Example

```text
target.py

scan.py

asset.py

report.py
```

Schemas should only validate data.

---

# app/repositories

Contains database repositories.

Example

```text
target_repository.py

scan_repository.py

asset_repository.py
```

Repositories:

- CRUD
- Queries
- Transactions

Repositories never contain business logic.

---

# app/services

Contains business logic.

Every module should expose one primary service.

Example

```text
target_service.py

scan_service.py

risk_service.py

report_service.py
```

Services orchestrate repositories and engines.

---

# app/scanners

Contains the Scanner Engine.

Structure

```text
scanners/

manager.py

factory.py

registry.py

executor.py

interfaces.py

artifacts.py

validators.py

adapters/

nmap.py

openvas.py
```

---

# app/parsers

Contains Parser Engine.

Structure

```text
parsers/

manager.py

factory.py

registry.py

interfaces.py

validators.py

normalizers.py

package_builder.py

parsers/

nmap_parser.py

openvas_parser.py
```

---

# app/risk_engine

Contains deterministic risk calculation.

Structure

```text
risk_engine/

coordinator.py

calculator.py

aggregator.py

rules.py

context.py
```

---

# app/ai

Contains AI abstraction.

Structure

```text
ai/

provider.py

manager.py

prompt_builder.py

response_validator.py

providers/

openrouter.py

groq.py

gemini.py
```

Business logic must never depend on provider implementations.

---

# app/reporting

Contains reporting implementation.

Structure

```text
reporting/

generator.py

templates.py

pdf.py

json_export.py
```

---

# app/dashboard

Contains dashboard aggregation.

Structure

```text
dashboard/

service.py

aggregator.py
```

---

# app/audit

Contains audit implementation.

Structure

```text
audit/

service.py

repository.py

events.py
```

---

# app/utils

Contains reusable utilities.

Utilities must:

- Be framework independent
- Be reusable
- Not duplicate standard library functionality

Utility modules should remain minimal.

---

# Tests

Mirror the application structure.

```text
tests/

api/

services/

repositories/

scanners/

parsers/

risk/

ai/

reporting/

dashboard/

audit/
```

Every production module should have corresponding tests.

---

# Scripts

Contains developer utilities.

Examples

```text
scripts/

seed_database.py

reset_database.py

generate_demo_data.py
```

Scripts must never be imported by application code.

---

# Alembic

Contains migration configuration.

Only Alembic should modify schema history.

---

# Configuration Files

Required files

```text
.env.example

pyproject.toml

README.md

.pre-commit-config.yaml

.editorconfig
```

Added during the Backend Hardening & Stabilization phase: `.pre-commit-config.yaml`
(ruff lint/format + mypy, run from `backend/`) and `.editorconfig`. Ruff-managed
lint/format/import-sort configuration and mypy configuration live in `pyproject.toml`
under `[tool.ruff]` and `[tool.mypy]`.

Future

```text
Dockerfile

docker-compose.yml

Makefile
```

---

# Dependency Direction

Dependencies always flow downward.

```text
Routes

↓

Services

↓

Repositories

↓

Database
```

Engines communicate only through Services.

No circular dependencies are permitted.

---

# Naming Conventions

Packages

snake_case

Files

snake_case

Classes

PascalCase

Functions

snake_case

Variables

snake_case

Constants

UPPER_CASE

Enums

PascalCase

---

# File Guidelines

Every file should have a single responsibility.

Prefer:

- Small files
- Small classes
- Small functions

Avoid:

- God classes
- Utility dumping
- Circular imports

---

# Import Rules

Prefer absolute imports.

Never use wildcard imports.

Imports should be grouped:

1. Standard Library
2. Third-party Libraries
3. Application Modules

---

# Module Boundaries

Each module owns its own:

- Service
- Repository
- Schemas
- Tests

Business logic must never leak across module boundaries.

---

# Future Scalability

The structure supports:

- Authentication
- RBAC
- Scheduling
- Distributed Workers
- Plugin System
- WebSockets
- Message Queues
- Cloud Connectors
- Multi-tenancy

These additions should integrate without restructuring the existing backend.

---

# Modification Policy

This directory structure is considered frozen.

Any structural change must:

- Be documented
- Be reviewed
- Preserve architecture consistency

No AI agent should reorganize the backend without explicit instruction.