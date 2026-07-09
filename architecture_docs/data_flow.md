# Data Flow Architecture

**File:** `architecture_docs/data_flow.md`

---

# Purpose

This document defines how data flows through the Automated Vulnerability Assessment Platform (AVAP).

It describes:

- Request lifecycle
- Scan lifecycle
- Internal component interactions
- Data ownership
- Processing boundaries
- Persistence flow

This document focuses on **data movement**, not implementation details.

Implementation specifications are documented in:

- `system_architecture.md`
- `backend/backend.md`
- `modules_docs/*`

---

# Data Flow Principles

The platform follows these principles:

- Single direction data flow
- Clear ownership of data
- Explicit processing stages
- No layer bypassing
- Immutable processing where practical
- Validation before persistence
- Normalization before business logic

Every component receives validated input and produces well-defined output.

---

# High-Level Data Flow

```
                User / Client
                      │
                      ▼
              REST API (FastAPI)
                      │
                      ▼
             Request Validation
                      │
                      ▼
              Business Service
                      │
                      ▼
             Target Validation
                      │
                      ▼
             Scan Management
                      │
                      ▼
             Scanner Engine
          ┌───────────┴───────────┐
          ▼                       ▼
        Nmap                 OpenVAS
          │                       │
          └───────────┬───────────┘
                      ▼
               Parser Engine
                      │
                      ▼
          Normalized Scan Models
                      │
          ┌───────────┼────────────┐
          ▼           ▼            ▼
 Asset Storage  Vulnerability DB  Metadata
          │
          ▼
          Risk Engine
          │
          ▼
        AI Engine
          │
          ▼
   Report Generation
          │
          ▼
      API Response
```

---

# Request Lifecycle

Every API request follows the same processing model.

```
Client Request
      │
      ▼
Route
      │
      ▼
Request Validation
      │
      ▼
Business Service
      │
      ▼
Repository / Scanner
      │
      ▼
Business Processing
      │
      ▼
Response Model
      │
      ▼
Client
```

---

# Target Submission Flow

When a scan request is submitted:

```
Client

↓

POST /targets

↓

Validate Request Schema

↓

Validate Target

↓

Normalize Target

↓

Store Target

↓

Return Target ID
```

Target validation includes:

- IP validation
- CIDR validation
- Hostname validation
- Duplicate detection
- Format normalization

---

# Scan Lifecycle

A scan progresses through multiple stages.

```
Target

↓

Create Scan Job

↓

Queued

↓

Scanner Execution

↓

Raw Results

↓

Parser

↓

Normalized Findings

↓

Database Storage

↓

Risk Assessment

↓

AI Analysis

↓

Report Generation

↓

Completed
```

---

# Scanner Data Flow

The Scanner Engine orchestrates all scanner interactions.

```
Scan Request

↓

Scanner Engine

↓

Scanner Adapter

↓

External Scanner

↓

Raw Output

↓

Parser
```

The Scanner Engine never interprets scanner output.

Its responsibilities are limited to:

- Scanner execution
- Process monitoring
- Exit status
- Timeout handling
- Result collection

---

# Parser Flow

Each scanner has its own parser.

```
Raw XML

↓

XML Parser

↓

Validation

↓

Normalization

↓

Internal Models
```

No raw scanner output enters business logic.

All findings are transformed into platform-specific models.

---

# Asset Discovery Flow

Assets discovered during scanning follow this process.

```
Parsed Asset

↓

Normalize

↓

Duplicate Detection

↓

Database Lookup

↓

Create / Update Asset

↓

Store Asset
```

Assets become the source of truth for future scans.

---

# Vulnerability Flow

Each discovered vulnerability follows:

```
Parsed Finding

↓

Validation

↓

Normalize

↓

CVE Extraction

↓

Severity Mapping

↓

Database Storage

↓

Risk Assessment
```

Future enhancements may enrich findings with:

- CVSS
- CWE
- EPSS
- CPE
- Vendor advisories

---

# Risk Assessment Flow

Risk calculation is deterministic.

```
Normalized Finding

↓

Risk Engine

↓

Calculate Severity

↓

Business Rules

↓

Risk Score

↓

Store Result
```

The Risk Engine does not use AI.

AI is invoked only after deterministic scoring.

---

# AI Analysis Flow

AI consumes normalized information only.

```
Finding

↓

Risk Score

↓

Context

↓

AI Provider

↓

Remediation Guidance

↓

Store Recommendation
```

AI cannot:

- modify findings
- alter risk score
- change database records

AI output is advisory.

---

# Report Generation Flow

Reports are generated using stored assessment data.

```
Scan ID

↓

Retrieve Data

↓

Assemble Report Model

↓

Generate PDF

↓

Store Report

↓

Return Download Path
```

Reports never use raw scanner output.

Only normalized data is included.

---

# Database Flow

Database interaction always occurs through repositories.

```
Service

↓

Repository

↓

SQLAlchemy

↓

PostgreSQL
```

Direct SQL execution outside repositories is prohibited.

---

# Error Flow

Errors propagate in a controlled manner.

```
Component

↓

Custom Exception

↓

Global Exception Handler

↓

API Response
```

Internal details are logged but never exposed to clients.

---

# Logging Flow

Every significant operation generates structured logs.

```
Operation

↓

Logger

↓

Structured Log Entry

↓

Log Sink
```

Examples:

- Scan started
- Scan completed
- Scanner failure
- Database error
- AI request
- Report generation

Sensitive information is never logged.

---

# Configuration Flow

Configuration is loaded once during application startup.

```
Environment Variables

↓

Configuration Module

↓

Application Components
```

Components do not load environment variables directly.

---

# Data Ownership

| Data | Owner |
|-------|-------|
| Request Payload | API Layer |
| Business State | Service Layer |
| Database Entities | Repository Layer |
| Raw Scanner Output | Scanner Engine |
| Normalized Findings | Parser Layer |
| Risk Score | Risk Engine |
| AI Recommendations | AI Engine |
| Reports | Reporting Engine |

Ownership must remain exclusive.

---

# Data Validation Flow

Validation occurs in multiple stages.

```
Client Input

↓

Pydantic Validation

↓

Business Validation

↓

Scanner Validation

↓

Parser Validation

↓

Database Constraints
```

Each stage validates only the rules it owns.

---

# Persistence Flow

Only normalized information is persisted.

```
Scanner Output

↓

Parser

↓

Normalized Models

↓

Repository

↓

Database
```

Raw scanner output may be retained temporarily for debugging or audit purposes but is never used directly by business logic.

---

# Future Asynchronous Flow

Current implementation executes scans synchronously from the perspective of orchestration.

Future versions may introduce asynchronous execution.

```
Create Scan

↓

Queue Job

↓

Worker

↓

Scanner

↓

Parser

↓

Risk Engine

↓

Report

↓

Notify User
```

This evolution should not require changes to the API contract.

---

# Future Distributed Flow

Future architecture may separate scanning from the API server.

```
API Server

↓

Job Queue

↓

Scanner Worker

↓

Result Queue

↓

Parser

↓

Database
```

The current architecture preserves this migration path by keeping scanner execution isolated behind the Scanner Engine.

---

# Data Integrity

The platform maintains integrity through:

- Request validation
- Business validation
- Normalization
- Repository abstraction
- Database constraints
- Foreign keys
- Transactions
- Deterministic processing

---

# Data Flow Summary

The platform enforces a predictable and secure flow of information:

1. Validate all external input.
2. Execute scanners through isolated adapters.
3. Parse and normalize all scanner output.
4. Persist only validated, normalized data.
5. Calculate deterministic risk scores.
6. Generate AI-assisted remediation as advisory information.
7. Produce reports from normalized database records.
8. Return structured responses through the REST API.

No component may bypass another layer, and every transition between stages represents a clearly defined processing boundary. This architecture ensures consistency, auditability, and extensibility while supporting future enhancements such as asynchronous execution, distributed scanning, and enterprise-scale deployments.