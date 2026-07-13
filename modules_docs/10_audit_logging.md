# Audit Logging Module

**Module:** 10 - Audit Logging

**File:** `modules_docs/10_audit_logging.md`

**Version:** 1.0

**Status:** Implemented

---

# Purpose

The Audit Logging module is responsible for recording immutable, chronological, and structured records of significant events occurring throughout the Automated Vulnerability Assessment Platform (AVAP).

Unlike application logging, which is intended for debugging and operational monitoring, audit logging provides a permanent record of security-relevant and business-critical events for traceability, accountability, compliance, and forensic analysis.

The Audit Logging module acts as the platform's **system of accountability**, ensuring that important actions can always be reconstructed.

---

# Objectives

The Audit Logging module is designed to:

* Record significant platform events
* Maintain immutable audit history
* Support forensic investigations
* Enable compliance reporting
* Provide complete traceability
* Track lifecycle events
* Record security-related operations
* Support future enterprise compliance requirements

---

# Responsibilities

The Audit Logging module is responsible for:

* Recording audit events
* Standardizing audit records
* Persisting audit logs
* Providing audit retrieval APIs
* Supporting event filtering
* Supporting historical event queries
* Recording system state transitions
* Recording module activities

The module is **not responsible for**:

* Application debugging
* Performance monitoring
* Metrics collection
* Risk calculation
* Scanner execution
* Business logic

---

# Design Principles

The Audit Logging module follows:

* Immutability
* Chronological Ordering
* Structured Logging
* Separation of Concerns
* High Integrity
* Tamper Resistance
* Minimal Performance Impact

Audit records must never be modified after creation.

---

# High-Level Architecture

```text
                    All Platform Modules
                            │
                            ▼
                  Audit Logging Interface
                            │
                            ▼
                   Audit Event Builder
                            │
                            ▼
                 Audit Validation Engine
                            │
                            ▼
                 Audit Repository Layer
                            │
                            ▼
                      PostgreSQL
                            │
                            ▼
                    Audit Retrieval APIs
```

---

# Internal Components

| Component           | Responsibility                    |
| ------------------- | --------------------------------- |
| Audit Coordinator   | Entry point of the module         |
| Audit Event Builder | Creates standardized audit events |
| Audit Validator     | Validates audit records           |
| Audit Repository    | Persists audit events             |
| Audit Query Service | Retrieves audit history           |
| Audit API           | Exposes audit endpoints           |

---

# Implemented Architecture and Scope

| Conceptual Component | Implementation |
|---|---|
| Audit Coordinator / Audit Event Builder / Audit Validator | `app/services/audit_service.py` (`AuditService.append_event`, `record_failure_safely`) + `app/audit/metadata_policy.py` (`validate_metadata`) |
| Audit Repository | `app/repositories/audit_repository.py` (`AuditRepository`) |
| Audit Query Service | `AuditService.get_event` / `list_events` |
| Audit API | `app/api/routes/v1/audit.py`, mounted at `/api/v1/audit` |
| Actor/request context | `app/audit/context.py` (`ActorContext`, `RequestContext`, `AuditContext`), resolved per-request by `app/api/dependencies/audit.py` |
| Request correlation | `app/api/middleware/request_context.py` |

## Naming: `AuditEvent`/`audit_events`, not `AuditLog`/`audit_logs`

This document's original "Database Ownership" section and
`backend/project_structure.md`'s illustrative sketch (`audit_log.py`) named
the table `audit_logs`. The implementation instead uses the model class
`AuditEvent` and table `audit_events` throughout — repository, service,
schemas, API, and tests. This is a deliberate naming choice, not an
oversight: it matches the terminology used consistently for every other
concept in this module (event type, event category, audit event lifecycle)
and avoids the word "log," which this document itself distinguishes sharply
from audit records ("Logging vs Audit Logging" below). No `audit_logs` table
or `AuditLog` class exists anywhere in the codebase.

## Guarantee levels (read this before relying on any immutability claim)

Four different guarantees are possible for an audit trail, and this
implementation provides exactly two of them:

| Guarantee | Provided? | Where |
|---|---|---|
| Application-level append-only (no update/delete code path) | Yes | `AuditRepository` has no `update()`/`delete()`/`upsert()`; no `PUT`/`PATCH`/`DELETE` route exists |
| Database-level append-only (UPDATE/DELETE physically rejected) | Yes, PostgreSQL only | Trigger `audit_events_no_update_delete` installed by migration `0007_audit_event`; **not exercised by the SQLite-based automated test suite**, verified instead by offline SQL compilation (`alembic upgrade head --sql`) and manual DDL review |
| Tamper-evident (hash chaining detects retroactive edits) | **No** | Not implemented — this document's own "Future Enhancements" section already lists "Tamper detection" and "Digital signatures" as future work, not current requirements |
| Cryptographically tamper-proof / WORM storage | **No** | Future work only |

Do not describe `AuditEvent` rows as tamper-proof, cryptographically
verified, or WORM beyond what this table states.

---

# Audit Event Lifecycle

Every audit event follows the same lifecycle.

```text
Platform Event

↓

Audit Event Builder

↓

Validation

↓

Repository

↓

Database

↓

Available for Query
```

Audit events are immutable after persistence.

---

# Audit Event Sources

Every major module may generate audit events.

Current sources include:

* Target Validation
* Scan Management
* Scanner Engine
* Parser Engine
* Asset & Vulnerability Management
* Risk Assessment
* AI Engine
* Reporting Engine
* Dashboard APIs
* System Startup
* System Shutdown

Future sources:

* Authentication
* RBAC
* Scheduler
* Plugin Manager
* User Management

---

# Auditable Events (implemented taxonomy)

The centralized `AuditEventType` enum (`app/core/enums.py`) defines exactly
these 15 values — no free-form event names are used anywhere. Only
orchestration-boundary outcomes are audited (never "started"/"requested"
intent-only events with no outcome yet, and never one event per child
row/asset/vulnerability):

## Target Events (`TargetService`)

* `TARGET_CREATED`, `TARGET_UPDATED`, `TARGET_DELETED` — all SUCCESS-only;
  a rejected create/update (duplicate, invalid format) is a normal 4xx
  business validation outcome, not a security-relevant failure worth
  auditing

## Scan Events (`ScanService`)

* `SCAN_CREATED`, `SCAN_DELETED` — SUCCESS-only. `SCAN_DELETED` is an
  additive entry beyond this document's original example list: deleting
  scan history is a genuine security-relevant mutation and is audited even
  though the original sparse example list omitted it. "Scan Started"/"Scan
  Completed"/"Scan Failed" are represented by `INVENTORY_PROCESSED`/
  `INVENTORY_PROCESSING_FAILED` below (see rationale).

## Inventory Events (`InventoryService`) — replaces per-entity Asset/Vulnerability events

* `INVENTORY_PROCESSED`, `INVENTORY_PROCESSING_FAILED` — one event per
  `process_assessment_package()` call, not one per asset/service/
  vulnerability/finding. This is the actual orchestration boundary that
  transitions `ScanJob.status` to `COMPLETED`/`FAILED` in this codebase, so
  it also stands in for "Scan Completed"/"Scan Failed" without emitting a
  duplicate event for the same underlying transaction. Auditing every
  discovered asset/vulnerability individually was rejected as audit-event
  flooding.

## Risk Events (`RiskService`)

* `RISK_CALCULATION_COMPLETED`, `RISK_CALCULATION_FAILED` — one event per
  `calculate_risk_for_scan()` call (covering vulnerability/asset/scan/
  assessment-scope recalculation as a single business action, not four
  separate events)

## AI Events (`AIService`)

* `AI_RECOMMENDATION_GENERATED` — SUCCESS, recorded both when a fresh
  recommendation is generated and when an existing current recommendation
  is idempotently reused (both represent "a current recommendation is now
  available" as the business outcome of the call)
* `AI_RECOMMENDATION_FAILED` — FAILURE, for AI provider failures and
  response-validation failures only (not for 404/422 request-input errors)

## Report Events (`ReportService`)

* `REPORT_GENERATED`, `REPORT_GENERATION_FAILED`, `REPORT_DOWNLOADED`,
  `REPORT_DELETED` — all four from this document's original example list
  are implemented

## Not currently integrated (disclosed, not silently dropped)

Scanner Events, Parser Events, and System Events (Application Started/
Shutdown, Configuration Loaded, Migration Executed) from this document's
original example list are **not implemented** in this increment: the
Scanner/Parser modules have no dedicated orchestration-boundary service
matching this integration pattern without invasive changes to Modules
03/04, and wiring `main.py` startup/shutdown events was out of scope for
the required Target/Scan/Inventory/Risk/AI/Report integration set. The
`SYSTEM` category exists in the enum for this future work.

---

# Audit Record Structure (implemented fields)

Every `AuditEvent` row (`app/models/audit_event.py`) contains:

* `id` (Audit ID)
* `occurred_at` (Timestamp, UTC, server-generated only — never accepted
  from an API caller)
* `event_type`, `category` (Event Type / Event Category — see taxonomy
  above; no separate "Operation" column exists since `event_type` already
  encodes the operation, e.g. `RISK_CALCULATION_COMPLETED`)
* `outcome` (Status: `SUCCESS` or `FAILURE` only — no `DENIED`/`PARTIAL`/
  `CANCELLED` values exist since no integrated operation has that semantic)
* `actor_type`, `actor_id` (see Actor Abstraction below)
* `resource_type`, `resource_id` — plain UUID column, **no foreign key**:
  audit evidence survives deletion of the resource it documents
* `scan_id` — plain UUID column, no foreign key, for scan-scoped queries
* `request_id`, `source_ip` — implemented now (see Request/Correlation
  Context below), not deferred to "Future fields" as originally listed
* `event_metadata` — JSONB (PostgreSQL) / JSON (SQLite), validated by the
  metadata security policy before persistence (see below)

"Event Summary" (a free-text description) is deliberately **not** a column:
this document's own principle — "Do not encode mutable human-readable
descriptions as the only event identity" — is honored by relying entirely
on the structured `event_type`/`category`/`outcome`/`resource_type` fields.

"User ID"/"Session ID"/"Tenant ID" remain future fields, unchanged: AVAP has
no authentication, users, or multi-tenancy yet.

---

# Event Categories

Implemented `AuditEventCategory` values (`app/core/enums.py`):

| Category  | Description                          | Emitted today? |
| --------- | ------------------------------------- | -------------- |
| SYSTEM    | Platform lifecycle                    | No — reserved for future startup/shutdown events |
| TARGET    | Target management                     | Yes |
| SCAN      | Scan lifecycle                        | Yes |
| INVENTORY | Asset/vulnerability/finding ingestion | Yes (replaces separate Scanner/Parser/Asset/Vulnerability categories — see "Auditable Events" above) |
| RISK      | Risk calculations                     | Yes |
| AI        | AI interactions                       | Yes |
| REPORT    | Report generation                     | Yes |

Scanner, Parser, Asset, Vulnerability, and Dashboard categories from this
document's original list are not implemented as separate categories: Scanner/
Parser/Asset/Vulnerability activity is represented at the coarser
`INVENTORY` category (see rationale above), and Dashboard GET requests are
explicitly **not** audited (ordinary read access is not a security-relevant
mutation; see "Data Flow" below).

Future categories may be introduced without changing existing APIs.

---

# REST APIs

Base endpoint:

```text
/api/v1/audit
```

---

## List Audit Events

```text
GET /audit
```

Returns a paginated, filtered list. Read-only: `POST`/`PUT`/`PATCH`/`DELETE`
are not implemented on this route — clients can never manufacture, edit, or
remove an audit record.

Query parameters (all optional, all validated):

* `skip` (int, ≥0, default 0), `limit` (int, 1–200, default 50)
* `event_type` (one of the 15 `AuditEventType` values)
* `category` (one of the `AuditEventCategory` values)
* `outcome` (`SUCCESS` or `FAILURE`)
* `resource_type` (one of the `AuditResourceType` values), `resource_id` (UUID)
* `scan_id` (UUID)
* `actor_type` (`SYSTEM` or `ANONYMOUS`)
* `occurred_after`, `occurred_before` (ISO-8601 UTC datetimes)

Ordering is always `occurred_at DESC, id DESC` (deterministic tie-break).
This document's original example filters (`module=`, `event=`, `status=`)
are superseded by the structured, validated parameter names above — no
generic filter/group-by/raw-SQL parameter is ever accepted.

---

## Get Audit Event

```text
GET /audit/{event_id}
```

Returns a specific audit record, or 404 if not found / 422 if `event_id`
is not a valid UUID.

---

# Data Flow

```text
Platform Module

↓

AuditService.append_event() (shared tx) or record_failure_safely() (fresh tx)

↓

AuditRepository.append()

↓

Database

↓

Audit API (GET only)

↓

Client
```

No module reads audit events during normal business processing — audit
data is observational only, and `AuditService` itself is never audited
(no recursive auditing). Dashboard GET requests, and ordinary list/detail
GET requests across every module, do not generate audit events.

---

# Logging vs Audit Logging

| Application Logging    | Audit Logging  |
| ---------------------- | -------------- |
| Operational            | Compliance     |
| Mutable retention      | Immutable      |
| Debugging              | Accountability |
| Performance monitoring | Event history  |
| Short-term             | Long-term      |

Application logs and audit logs must remain separate.

---

# Actor Abstraction

AVAP has no authentication, users, or RBAC. `AuditActorType` (`app/core/enums.py`)
defines exactly two values:

* `SYSTEM` — internal orchestration invoked with no HTTP caller (the default
  when a service's optional `audit_context` parameter is omitted, e.g. direct
  test/internal invocation)
* `ANONYMOUS` — every current HTTP-triggered action (resolved by
  `get_audit_context` in `app/api/dependencies/audit.py`)

`actor_id` is always `None` for both — no fake username, no hardcoded
"admin", and no client-supplied header (`X-User`, `X-Username`, `X-Actor-ID`,
etc.) is ever read as a trusted actor identity. `AUTHENTICATED_USER` is
deliberately not yet defined in the enum; adding it once real authentication
exists is a backward-compatible enum extension, not a redesign of
`AuditService`.

# Request/Correlation Context

`app/api/middleware/request_context.py` resolves a per-request ID: a
well-formed inbound `X-Request-ID` (alphanumeric + hyphen, ≤100 chars) is
reused; anything absent, oversized, or containing disallowed characters is
replaced with a fresh server-generated UUID4. The resolved ID is stored on
`request.state` and echoed back via the `X-Request-ID` response header. No
second competing correlation-ID mechanism exists.

`source_ip` is always `Request.client.host` — the direct ASGI connection
address. `X-Forwarded-For` and `X-Real-IP` are never read or trusted, since
no trusted reverse-proxy configuration is documented for this deployment.

# Transaction Semantics

See `backend/backend.md`'s "Audit event transaction pattern" section for
the full description. Summary:

* **SUCCESS events** are appended (flush-only) inside the same transaction
  as the business action they document, before that transaction's own
  commit, for every service that owns an explicit transaction (`RiskService`,
  `AIService`, `ReportService`, `InventoryService`). An audit failure there
  rolls back the business action too — no false SUCCESS is possible.
* **FAILURE events** are recorded via `AuditService.record_failure_safely()`
  in a fresh transaction after the business rollback, and this method never
  raises — an audit-subsystem failure while recording a failure event is
  logged and swallowed, never replacing the original business exception.
* **`TargetService`/`ScanService`** are a disclosed exception: their
  repositories (`TargetRepository`, `ScanRepository`) commit synchronously
  inside `create`/`update`/`delete` — a pre-Module-10 pattern not redesigned
  here. Their audit events are therefore best-effort, appended immediately
  after the already-committed mutation; an audit failure there is logged
  and swallowed, since the business action cannot be rolled back at that
  point. This is a real, intentional trust-boundary limitation, not a
  falsely-claimed fail-closed guarantee.

# Metadata Security Policy

`app/audit/metadata_policy.py` validates every metadata dict before
`AuditService` persists it — rejecting rather than sanitizing:

* Max nesting depth 2 (one level of dict nesting beyond the top level)
* Max 20 keys per level, max key length 100, max string value length 500
* Only `str`/`int`/`float`/`bool`/`None`/one-level-nested `dict` values are
  accepted — lists, ORM objects, exceptions, and any other object type are
  rejected
* A case-insensitive, recursively-checked forbidden-key list (`authorization`,
  `password`, `passwd`, `secret`, `secret_key`, `token`, `access_token`,
  `refresh_token`, `api_key`, `apikey`, `cookie`, `set-cookie`,
  `database_url`, `private_key`, and normalized variants)

Metadata is always server-generated by the integrating service — never
`request.dict()`, `model_dump()`, `vars()`, or an exception's `__dict__`.
AI provider/model/prompt-version identifiers are legitimate metadata; AI
prompts, system messages, provider response bodies, summaries,
explanations, remediation/validation steps, and cautions are never
persisted. Report metadata contains format/counts/sizes only — never a
file name, absolute path, or temporary path.

# Security Requirements

The Audit Logging module:

* Prevents modification of existing audit records (application-level
  always; database-level trigger on PostgreSQL — see "Guarantee levels" above)
* Timestamps every event server-side (`occurred_at`, never client-supplied)
* Validates audit metadata recursively before persistence
* Prevents audit injection (no client-controlled event type/category/
  metadata reaches persistence — metadata is never built from request data)
* Digital signing remains future work, not claimed as implemented

Audit records never contain:

* Passwords, API keys, secrets, tokens, private keys
* AI prompts, system messages, or provider response bodies
* AI recommendation summaries, explanations, remediation/validation
  steps, or cautions
* Report file names, absolute paths, or temporary paths
* Raw exception messages or stack traces (failure metadata uses
  `failure_category: type(exc).__name__` only)

---

# Database Ownership

Primary table:

```text
audit_events
```

(See "Naming" above for why this differs from this document's original
`audit_logs` name.)

The module owns:

* `AuditEvent` rows and their `event_metadata` JSONB/JSON column

`resource_id`/`scan_id` are plain UUID columns with **no foreign key** —
deleting a Target, Scan, Report, etc. never cascades into deleting the
audit events that documented actions against it. Verified: no
`ForeignKeyConstraint` exists for either column in migration
`0007_audit_event.py`.

Audit tables are append-only (see "Guarantee levels" above for the exact
enforcement level).

---

# Performance Considerations

The Audit Logging module should:

* Minimize write latency
* Batch writes where appropriate
* Avoid blocking business workflows
* Support asynchronous persistence (future)

Future versions may introduce event queues without modifying the public API.

---

# Dependencies

Depends on:

* Repository Layer
* Configuration Module
* Logging Module

Communicates with:

* PostgreSQL

Receives events from:

* Every platform module

The Audit Logging module must never influence business logic.

---

# Future Enhancements

The architecture supports:

* Digital signatures
* Tamper detection
* WORM storage
* External SIEM integration
* Syslog export
* OpenTelemetry support
* Event streaming
* Compliance reports
* Immutable object storage
* Centralized audit service
* Multi-tenant audit isolation

These enhancements should integrate without changing the audit event model.

---

# Testing Requirements (as implemented)

## Context / Metadata Policy Tests (`tests/audit/`, 36 tests)

Actor/request context immutability and factory behavior; recursive
forbidden-key rejection (case-insensitive, nested), size/depth/type bounds,
ORM-object/exception/list rejection.

## Repository Tests (`tests/repositories/test_audit_repository.py`, 17 tests)

Append, get-by-ID, no update/delete/upsert method exists, no-commit
behavior, every filter (event type, category, outcome, resource, scan,
actor, date range), deterministic ordering, pagination, empty-database
behavior.

## Service Tests (`tests/services/test_audit_service.py`, 10 tests)

Successful append with validated actor/request context, SYSTEM vs
ANONYMOUS context, server-generated `occurred_at` (no such parameter
exists in `append_event`'s signature), unsafe metadata rejected before
persistence, `record_failure_safely` never raises and persists durably
even when metadata would otherwise be unsafe, retrieval/empty-state
behavior.

## Transaction Semantics Tests (`tests/services/test_audit_transaction_semantics.py`, 16 tests)

Per integrated service (Target/Scan/Inventory/Risk/AI/Report): SUCCESS
event persisted with the correct resource ID; an audit persistence failure
during a shared-transaction SUCCESS path rolls back the business data
(verified via actual row counts, not mocks); FAILURE events survive the
business rollback; TargetService's documented best-effort/post-commit
exception verified explicitly; no duplicate event from AIService's
idempotent short-circuit path (exactly one event per call, not one per
provider invocation).

## API Tests (`tests/api/test_audit_api.py`, 18 tests)

List/retrieve, every filter, pagination, invalid UUID/date range, empty
database, `POST`/`PUT`/`PATCH`/`DELETE` all rejected with 405, no
secret/path exposure.

## Actor/Request Context Security Tests (`tests/api/test_audit_context_security.py`, 8 tests)

Exercised through the real HTTP stack: request ID generated when absent,
valid inbound ID reused, oversized/control-character/malformed IDs
replaced; `X-Forwarded-For`/`X-Real-IP` never change the recorded
`source_ip`; `X-User`/`X-Username`/`X-Actor-ID` headers never produce an
impersonated actor.

## Full Lifecycle Integration Test (`tests/services/test_audit_integration.py`, 1 test)

Target creation → Scan creation → Inventory processing → Risk calculation
→ AI recommendation generation (fake provider boundary) → Report
generation, all through the real REST API, followed by Audit API
retrieval verifying: every expected event type present, deterministic
ordering, correct resource/scan correlation, correct actor semantics,
all-SUCCESS outcomes, and the complete absence of AI content, secrets,
and file paths anywhere in the audit trail.

All APIs are directly testable via the existing FastAPI `TestClient`-backed
suite above; no separate Postman collection artifact was produced for this
increment.

---

# Definition of Done

The Audit Logging module is complete:

* `AuditService`/`AuditRepository` implemented (`append_event`,
  `record_failure_safely`, `get_event`, `list_events`)
* REST APIs completed — `GET /audit`, `GET /audit/{event_id}`, no
  create/update/delete endpoint
* Application-level append-only verified (no repository mutation methods);
  database-level append-only verified via PostgreSQL trigger + offline SQL
  compilation
* 106 new tests added (36 context/metadata + 17 repository + 10 service +
  16 transaction semantics + 18 API + 8 context security + 1 full
  lifecycle integration); complete backend regression: 555 passed, 0
  failed (449-test baseline + 106), verified on Python 3.12.13 and 3.14.6
* Documentation updated (this file, plus `architecture_docs/database.md`,
  `architecture_docs/security.md`, `backend/backend.md`)

Completion of this module marks the completion of the initial backend implementation phase.

---

# Related Documentation

* `modules_docs/09_dashboard.md`
* `architecture_docs/system_architecture.md`
* `architecture_docs/data_flow.md`
* `architecture_docs/database.md`
* `architecture_docs/security.md`
* `architecture_docs/development_standards.md`
* `backend/backend.md`
* `ai_contract.md`
