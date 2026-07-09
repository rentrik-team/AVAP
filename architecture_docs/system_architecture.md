# System Architecture

**Project:** Automated Vulnerability Assessment Platform (AVAP)

**Version:** 1.0

**Status:** Active

---

# Purpose

This document defines the overall system architecture of the Automated Vulnerability Assessment Platform (AVAP).

It provides a high-level architectural view of the platform, its major components, communication boundaries, dependency rules, and extensibility model.

Detailed implementation specifications are documented separately within:

- backend/
- modules_docs/
- database.md
- security.md
- data_flow.md
- development_standards.md

---

# System Overview

The Automated Vulnerability Assessment Platform (AVAP) is a modular backend application that orchestrates multiple open-source security tools to automate the vulnerability assessment lifecycle.

The platform provides a single interface for:

- Target validation
- Asset discovery
- Port and service enumeration
- Vulnerability assessment
- Risk analysis
- AI-assisted remediation
- Report generation

The architecture is intentionally designed to support future enterprise features such as authentication, RBAC, scheduling, distributed scanners, and multi-tenancy without requiring significant architectural redesign.

---

# Architectural Goals

The system is designed with the following objectives:

- Modular architecture
- High maintainability
- Security-first design
- Scalability
- Loose coupling
- Strong separation of concerns
- Technology independence
- AI provider abstraction
- Scanner independence
- Testability

---

# Architectural Style

The platform follows a layered monolithic architecture.

This approach provides:

- Clear dependency boundaries
- Simpler deployment
- Easier testing
- Lower operational complexity
- Straightforward migration to microservices in the future

Current architecture intentionally avoids unnecessary distributed complexity.

---

# High-Level Architecture

```

                        Client (Future)

                               │

                               ▼

                    REST API (FastAPI)

                               │

                               ▼

                     Business Services

                               │

        ┌──────────────────────┼─────────────────────┐

        ▼                      ▼                     ▼

Repositories          Scanner Engine         Reporting Engine

        │                      │

        ▼                      ▼

 PostgreSQL            Parser Engine

                               │

                               ▼

                     Asset Management

                               │

                               ▼

                       Risk Engine

                               │

                               ▼

                         AI Engine

```

---

# Architectural Layers

The platform is organized into the following logical layers.

## Presentation Layer

Responsible for:

- REST APIs
- Request validation
- Response serialization

Technology:

- FastAPI
- Pydantic

Responsibilities:

- Validate requests
- Call services
- Return responses

No business logic exists here.

---

## Business Layer

Responsible for:

- Workflow orchestration
- Business rules
- Validation beyond schema checks

Components:

- Target Service
- Scan Service
- Risk Service
- Report Service

This layer represents the core of the platform.

---

## Persistence Layer

Responsible for:

- Database operations
- CRUD
- Transactions

Components:

- SQLAlchemy
- Repository classes

Business logic never interacts directly with the database.

---

## Infrastructure Layer

Responsible for external integrations.

Includes:

- Nmap
- OpenVAS
- AI Providers
- PDF Generation

Infrastructure components are isolated behind abstraction layers.

---

# Major Components

The platform consists of ten primary functional modules.

| Module | Responsibility |
|---------|---------------|
| Target Validation | Validate scan targets |
| Scan Management | Manage scan lifecycle |
| Scanner Engine | Execute scanners |
| Parser Engine | Normalize scanner output |
| Asset & Vulnerability Management | Store discovered assets and findings |
| Risk Assessment | Calculate deterministic risk |
| AI Engine | Generate remediation guidance |
| Reporting | Generate professional reports |
| Dashboard APIs | Provide aggregated data |
| Audit Logging | Record system events |

Each module is independently documented under `modules_docs`.

---

# Component Dependency

The following dependency rules are mandatory.

```

API

↓

Services

↓

Repositories

↓

Database

```

Scanner execution follows:

```

Services

↓

Scanner Engine

↓

Scanner Adapter

↓

Scanner

↓

Parser

↓

Normalized Models

```

Risk calculation follows:

```

Normalized Findings

↓

Risk Engine

↓

Risk Score

↓

AI Engine

↓

Report Generation

```

No component may bypass its designated abstraction layer.

---

# Component Communication

Components communicate synchronously using direct service calls.

Current communication pattern:

```

Route

↓

Service

↓

Repository

```

Future asynchronous processing may be introduced for long-running scans without affecting business logic.

---

# AI Architecture

AI functionality is isolated behind an abstraction layer.

```

Business Logic

↓

AI Interface

↓

Provider

↓

OpenRouter

Groq

Gemini

HuggingFace

```

Business logic remains provider-independent.

---

# Scanner Architecture

Each scanner is encapsulated within its own adapter.

```

Scanner Engine

↓

Scanner Adapter

↓

Nmap

```

```

Scanner Engine

↓

Scanner Adapter

↓

OpenVAS

```

Future scanners can be added without modifying existing modules.

---

# Parser Architecture

Each scanner has an associated parser.

```

Raw Output

↓

Parser

↓

Normalized Model

↓

Database

```

Business logic never consumes raw scanner output.

---

# Data Ownership

Each layer owns specific responsibilities.

| Layer | Owns |
|--------|------|
| API | Request validation |
| Services | Business logic |
| Repository | Database access |
| Parser | Data normalization |
| Risk Engine | Risk calculations |
| AI Engine | AI interactions |
| Reporting | Report generation |

Responsibilities must not overlap.

---

# Package Organization

The backend follows a modular package structure.

```
app/

api/

services/

repositories/

models/

schemas/

database/

core/

scanner/

parser/

risk_engine/

ai/

reporting/

middleware/

exceptions/

utils/
```

Each package has a single responsibility.

---

# Dependency Rules

Allowed:

```

API → Services

Services → Repository

Services → Scanner Engine

Services → Risk Engine

Services → AI Engine

Repository → Database

```

Forbidden:

```

API → Database

API → Scanner

Repository → Scanner

Parser → Database

AI → Database

Scanner → Repository

```

---

# Error Flow

Errors propagate through centralized exception handling.

```

Component

↓

Custom Exception

↓

Global Exception Handler

↓

HTTP Response

```

Internal implementation details are never exposed.

---

# Configuration

Configuration is centralized.

Sources:

- Environment variables
- Configuration module

No component loads configuration independently.

---

# Logging

Every significant operation should generate structured logs.

Logging responsibilities include:

- Scan execution
- Database failures
- AI requests
- Report generation
- System startup
- Unexpected exceptions

Sensitive information must never be logged.

---

# Extensibility

The architecture is intentionally designed for future expansion.

Planned capabilities include:

- Authentication
- RBAC
- Scheduler
- Multi-user support
- Distributed scan workers
- Plugin system
- Compliance modules
- Cloud scanning
- Threat intelligence integration

These features should integrate without modifying existing business logic.

---

# Scalability Strategy

Current architecture is a modular monolith.

This provides:

- Simplified deployment
- Easier debugging
- Faster development
- Lower operational overhead

Future migration to microservices can occur by extracting bounded contexts such as:

- Scanner Service
- AI Service
- Reporting Service

No current implementation should prevent this evolution.

---

# Design Principles

The architecture adheres to the following principles:

- Single Responsibility Principle
- Dependency Inversion Principle
- Separation of Concerns
- Explicit Dependencies
- Composition over Inheritance
- Interface-based Design
- Security by Design
- Fail Securely
- Loose Coupling
- High Cohesion

---

# Architecture Decision Summary

| Decision | Rationale |
|----------|-----------|
| Modular Monolith | Simpler development and deployment while maintaining clear boundaries |
| Layered Architecture | Enforces separation of concerns and maintainability |
| FastAPI | High-performance asynchronous REST framework with strong typing |
| PostgreSQL | Mature relational database with ACID guarantees |
| SQLAlchemy ORM | Type-safe ORM with Alembic migration support |
| Repository Pattern | Isolates persistence from business logic |
| AI Provider Abstraction | Prevents vendor lock-in and simplifies provider changes |
| Scanner Adapter Pattern | Enables integration of multiple scanners without affecting business logic |
| Parser Layer | Normalizes heterogeneous scanner outputs into a common model |
| Rule-Based Risk Engine | Ensures deterministic, auditable risk calculations independent of AI |
| AI as Advisory Layer | Keeps AI recommendations separate from authoritative risk assessment |
| Modular Documentation | Prevents duplication and keeps responsibilities isolated across documentation |

---

# Related Documentation

- `project.md` — Project overview and roadmap
- `ai_contract.md` — Governing engineering contract
- `architecture_docs/data_flow.md` — End-to-end request and scan workflows
- `architecture_docs/database.md` — Database architecture and schema design
- `architecture_docs/security.md` — Security architecture and trust boundaries
- `architecture_docs/development_standards.md` — Coding conventions and engineering standards
- `backend/backend.md` — Backend implementation architecture
- `modules_docs/` — Detailed specifications for each functional module