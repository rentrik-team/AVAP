# Development Standards


# Purpose

This document defines the development standards for the Automated Vulnerability Assessment Platform (AVAP).

Its objective is to ensure consistency, maintainability, readability, security, and scalability throughout the codebase.

Every contributor, whether human or AI, must follow these standards.

---

# General Principles

The project follows:

- SOLID
- DRY
- KISS
- Clean Architecture
- Separation of Concerns
- Explicit over Implicit
- Composition over Inheritance

Development should always prioritize:

1. Security
2. Maintainability
3. Readability
4. Extensibility
5. Reliability
6. Performance

---

# Repository Structure

```
project_root/

├── app/
│
├── alembic/
│
├── tests/
│
├── scripts/
│
├── docs/
│
├── .env
├── .env.example
├── requirements.txt
├── pyproject.toml
└── README.md
```

The repository should remain organized by responsibility.

No unrelated files should exist in the project root.

---

# Backend Folder Structure

```
app/

├── api/
│
├── core/
│
├── services/
│
├── repositories/
│
├── models/
│
├── schemas/
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
├── database/
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
```

Each directory must have a single responsibility.

---

# Layer Responsibilities

## API

Responsible for:

- Request validation
- Response serialization
- Calling services

Must never contain business logic.

---

## Services

Responsible for:

- Business logic
- Workflow orchestration
- Validation beyond request schemas

Services may call:

- repositories
- scanners
- parsers
- risk engine
- AI engine
- reporting engine

---

## Repositories

Responsible only for:

- CRUD operations
- Database queries

Repositories must never contain business logic.

---

## Models

Contains SQLAlchemy ORM models.

Only database representation belongs here.

---

## Schemas

Contains Pydantic request and response models.

Schemas should never interact with the database.

---

## Scanners

Responsible for scanner integrations.

Every scanner should have its own adapter.

---

## Parsers

Responsible for converting raw scanner output into normalized models.

---

## Risk Engine

Responsible for deterministic risk calculations.

---

## AI

Responsible for AI provider abstraction and AI-assisted remediation.

---

## Reporting

Responsible for generating reports.

---

# Naming Conventions

## Files

Use:

snake_case.py

Examples:

```
target_service.py
scan_repository.py
risk_engine.py
openvas_adapter.py
```

Never use:

```
TargetService.py
Target_Service.py
Targetservice.py
```

---

## Folders

Use lowercase snake_case.

Examples:

```
risk_engine
audit_logging
scanner_engine
```

---

## Classes

Use PascalCase.

Examples:

```
TargetService
RiskCalculator
OpenVASAdapter
PDFReportGenerator
```

---

## Functions

Use snake_case.

Examples:

```
create_scan()
calculate_risk()
generate_report()
```

---

## Variables

Use descriptive snake_case.

Good:

```
scan_result
risk_score
asset_id
```

Avoid:

```
x
obj
temp
```

---

## Constants

Use UPPER_CASE.

```
MAX_SCAN_TIMEOUT
DEFAULT_PAGE_SIZE
SUPPORTED_SCANNERS
```

---

## Enum Names

Use PascalCase.

```
ScanStatus
Severity
AssetType
```

Enum members:

```
PENDING
RUNNING
FAILED
COMPLETED
```

---

# API Naming

Base URL:

```
/api/v1/
```

Resources use plural nouns.

Examples:

```
/targets
/scans
/assets
/vulnerabilities
/reports
```

Avoid verbs in URLs.

Good:

```
POST /targets

GET /targets

DELETE /targets/{id}
```

Bad:

```
/createTarget

/getAllTargets

/deleteScan
```

---

# Database Naming

## Tables

Plural snake_case.

```
targets
scan_jobs
scan_results
assets
vulnerabilities
reports
```

---

## Columns

snake_case.

```
created_at
updated_at
scan_status
asset_type
```

---

## Primary Keys

```
id
```

---

## Foreign Keys

```
target_id
scan_job_id
asset_id
```

---

## Indexes

Use descriptive names.

```
idx_targets_ip

idx_assets_hostname
```

---

# SQLAlchemy Models

One model per file.

Example:

```
models/

target.py

scan_job.py

asset.py
```

Model names:

```
Target

ScanJob

Asset
```

---

# Pydantic Schemas

Naming convention:

Requests:

```
CreateTargetRequest

UpdateTargetRequest

ScanRequest
```

Responses:

```
TargetResponse

ScanResponse

AssetResponse
```

Collections:

```
TargetListResponse

ScanListResponse
```

---

# Repository Naming

```
TargetRepository

ScanRepository

AssetRepository
```

Repository files:

```
target_repository.py

scan_repository.py
```

---

# Service Naming

```
TargetService

ScanService

RiskService
```

Files:

```
target_service.py

scan_service.py
```

---

# Exception Naming

Custom exceptions should end with:

```
Exception
```

Examples:

```
TargetNotFoundException

ScanAlreadyRunningException

InvalidIPAddressException
```

---

# Logging Standards

Use structured logging.

Every log should include:

- Timestamp
- Module
- Severity
- Operation
- Context

Never log:

- API keys
- Passwords
- Tokens
- Secrets
- Database credentials

---

# Error Handling

Errors should:

- be descriptive
- never leak implementation details
- be centralized
- use custom exceptions where appropriate

Avoid generic Exception unless absolutely necessary.

---

# Import Rules

Import order:

1. Standard library

2. Third-party packages

3. Internal modules

Example:

```python
from pathlib import Path

from fastapi import APIRouter

from app.services.target_service import TargetService
```

Avoid wildcard imports.

```
from module import *
```

is prohibited.

---

# Dependency Injection

Always use dependency injection.

Never instantiate repositories directly inside routes.

Correct:

```
Route

↓

Service

↓

Repository
```

---

# Configuration

Configuration must originate from:

```
.env
```

Never hardcode:

- URLs
- Ports
- Credentials
- Tokens

---

# Security Standards

Every input is considered untrusted.

Validate:

- IP addresses
- Hostnames
- File paths
- UUIDs
- User input
- Query parameters

Never use:

- shell=True
- eval()
- exec()

Always use parameterized queries.

---

# Testing Standards

Every module must include:

- Unit tests
- Integration tests
- API tests

Tests mirror project structure.

Example:

```
tests/

services/

repositories/

api/

risk_engine/
```

---

# Documentation Standards

Public classes require docstrings.

Complex business logic should include explanatory comments.

Avoid obvious comments.

Good:

```
Calculate the highest CVSS score among duplicate findings.
```

Bad:

```
Increment i.
```

---

# Code Formatting

Follow:

- PEP 8
- Black formatting
- isort import ordering

Maximum line length:

```
88 characters
```

---

# Type Hints

Type hints are mandatory.

Example:

```python
def calculate_risk(score: float) -> int:
```

Avoid untyped functions.

---

# Asynchronous Code

Use async only when beneficial.

Avoid unnecessary async functions.

CPU-intensive work should remain synchronous unless delegated to background workers.

---

# File Size Guidelines

Recommended maximums:

| Component | Maximum |
|-----------|----------|
| Route | 250 lines |
| Service | 400 lines |
| Repository | 300 lines |
| Model | 250 lines |
| Schema | 250 lines |

Split files before they become difficult to navigate.

---

# Code Review Checklist

Before merging, verify:

- Naming conventions followed
- No business logic in routes
- Repository only accesses database
- Tests added
- Documentation updated
- Type hints present
- Security validation implemented
- Logging added where appropriate
- No duplicated code
- No hardcoded secrets
- No circular dependencies

---

# Definition of Quality

Code is considered production-ready only if it is:

- Secure
- Readable
- Maintainable
- Modular
- Testable
- Documented
- Consistent with project architecture

Every contribution should leave the codebase cleaner than it was before.


# Code Generation Standards

The objective of code generation is to produce production-quality software while minimizing unnecessary complexity.

## Prefer Standard Libraries

Always prefer mature, well-maintained, and secure standard or community-adopted libraries over custom implementations.

Do not reimplement functionality that is already provided by the language runtime or a widely accepted library unless there is a strong architectural or security justification.

Examples:

- Use `pathlib` instead of manually manipulating file paths.
- Use `ipaddress` for IP and CIDR validation.
- Use `uuid` for UUID generation.
- Use `datetime` for date handling.
- Use `subprocess` safely instead of custom process wrappers.
- Use SQLAlchemy ORM instead of manually constructing SQL.
- Use Pydantic for validation instead of custom validation code.
- Use FastAPI dependency injection instead of custom service locators.
- Use ReportLab APIs directly instead of manually generating PDF structures.

---

## Avoid Reinventing Existing Solutions

Before implementing custom logic, determine whether the required functionality already exists in:

- Python Standard Library
- FastAPI
- SQLAlchemy
- Pydantic
- Alembic
- PostgreSQL
- Official SDKs
- Well-maintained open-source libraries

Custom implementations should only be written when:

- Existing libraries cannot satisfy the requirement.
- Security requirements demand a custom solution.
- Architectural constraints require abstraction.
- Performance profiling demonstrates a need.

Convenience alone is not a sufficient reason to write custom implementations.

---

## Keep Implementations Minimal

Generated code should contain only what is necessary to satisfy the current requirement.

Avoid:

- Dead code
- Placeholder methods
- Unused helper functions
- Premature abstractions
- Unused configuration
- Speculative future features
- Redundant wrapper classes

Every class, function, and file should have a clear purpose.

---

## Follow Existing Framework Conventions

Prefer framework-native solutions over custom implementations.

Examples:

- FastAPI dependency injection
- FastAPI exception handlers
- SQLAlchemy session management
- Alembic migrations
- Pydantic validators
- Python logging module

Do not replace standard framework capabilities with custom implementations unless there is a documented architectural reason.

---

## Minimize Lines of Code Responsibly

The objective is not simply fewer lines of code, but fewer lines of maintainable, readable, and secure code.

Prefer:

- Clear implementations
- Standard APIs
- Built-in abstractions
- Reusable components

Avoid reducing readability solely to decrease line count.

---

## Evaluate Libraries Before Adoption

Before introducing a third-party library, verify that it:

- Is actively maintained.
- Has a strong community.
- Has acceptable security history.
- Is production-ready.
- Is compatible with the project license.
- Solves a meaningful problem.

Avoid adding dependencies for trivial functionality.

---

## Favor Composition Over Utility Proliferation

Do not create helper or utility modules unless the logic is genuinely reusable across multiple components.

Avoid creating utility functions that merely wrap existing library functionality without adding value.

---

## Production-First Code

Every generated implementation should:

- Use the simplest secure solution.
- Leverage existing framework capabilities.
- Minimize custom infrastructure.
- Remain easy to test.
- Remain easy to maintain.