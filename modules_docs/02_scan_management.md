# Scan Management Module

**Module:** 02 - Scan Management

**File:** `modules_docs/02_scan_management.md`

**Version:** 1.0

**Status:** Planned

---

# Purpose

The Scan Management module is responsible for orchestrating the lifecycle of vulnerability assessment jobs.

It acts as the coordination layer between validated targets and the Scanner Engine by creating, managing, tracking, and monitoring scan executions.

This module **does not perform scanning**.

Scanner execution is delegated to the Scanner Engine.

---

# Module Responsibilities

The Scan Management module is responsible for:

- Creating scan jobs
- Validating scan requests
- Associating scan jobs with targets
- Tracking scan status
- Coordinating scanner execution
- Monitoring scan progress
- Handling scan completion
- Recording scan metadata
- Providing scan lifecycle APIs

The module is **not responsible for**:

- Running scanners
- Parsing scanner output
- Calculating risk
- AI remediation
- Report generation

---

# Scan Lifecycle

Every scan progresses through a defined lifecycle.

```
Target

↓

Create Scan

↓

Pending

↓

Running

↓

Completed

↓

Results Available
```

Failure path:

```
Running

↓

Failed

↓

Error Recorded
```

Future lifecycle:

```
Pending

↓

Queued

↓

Running

↓

Paused

↓

Cancelled

↓

Completed

↓

Archived
```

---

# Scan States

The platform currently supports the following states.

| State | Description |
|---------|-------------|
| Pending | Scan created but not started |
| Running | Scanner currently executing |
| Completed | Scan completed successfully |
| Failed | Scan terminated due to an error |

Future states:

- Queued
- Scheduled
- Paused
- Cancelled
- Retrying
- Expired

---

# Business Rules

The Scan Management module enforces the following rules.

- A scan must reference an existing validated target.
- A scan cannot exist without a target.
- Every scan receives a unique identifier.
- Every scan records timestamps.
- Scan status changes must follow the defined lifecycle.
- Scanner execution must only occur through the Scanner Engine.
- Historical scan records must never be overwritten.

---

# Module Workflow

```
Client

↓

POST /scans

↓

Validate Request

↓

Verify Target Exists

↓

Create Scan Job

↓

Persist Scan Job

↓

Invoke Scanner Engine

↓

Monitor Execution

↓

Update Scan Status

↓

Return Response
```

---

# Component Interaction

```
API

↓

Scan Service

↓

Scan Repository

↓

Database
```

Scanner execution:

```
Scan Service

↓

Scanner Engine

↓

Scanner Adapter

↓

Nmap/OpenVAS
```

---

# Database Ownership

Primary entity:

```
ScanJob
```

Primary table:

```
scan_jobs
```

The Scan Management module owns all CRUD operations related to scan jobs.

---

# Stored Metadata

Every scan job should record:

- Scan ID
- Target ID
- Scan Status
- Scan Type
- Requested At
- Started At
- Completed At
- Execution Duration
- Failure Reason (if applicable)

Future fields:

- Scheduled Time
- Trigger Source
- Priority
- Worker ID
- Queue Position

---

# REST API

Base endpoint

```
/api/v1/scans
```

---

## Create Scan

```
POST /scans
```

Creates a new scan job.

---

## List Scans

```
GET /scans
```

Returns all scans.

Future versions should support pagination and filtering.

---

## Get Scan

```
GET /scans/{scan_id}
```

Returns scan details.

---

## Delete Scan

```
DELETE /scans/{scan_id}
```

Removes scan metadata.

Historical scan data should be retained according to future retention policies.

---

## Get Scan Status

```
GET /scans/{scan_id}/status
```

Returns current execution status.

---

## Retry Scan (Future)

```
POST /scans/{scan_id}/retry
```

Recreates a failed scan.

---

## Cancel Scan (Future)

```
POST /scans/{scan_id}/cancel
```

Cancels a running scan.

---

# Request Model

Example:

```json
{
    "target_id": 5
}
```

Future fields:

```json
{
    "target_id": 5,
    "scan_profile": "full",
    "priority": "normal"
}
```

---

# Response Model

Example

```json
{
    "scan_id": 101,
    "target_id": 5,
    "status": "pending",
    "created_at": "...",
    "updated_at": "..."
}
```

---

# Security Requirements

The module shall:

- Verify target existence.
- Reject invalid target identifiers.
- Reject duplicate running scans for the same target (configurable).
- Validate every request.
- Prevent unauthorized scanner invocation.
- Record all scan state transitions.

The module must never execute shell commands directly.

---

# Error Handling

Possible responses:

| Status | Description |
|----------|-------------|
| 400 | Invalid request |
| 404 | Target not found |
| 409 | Scan already running |
| 422 | Validation failed |
| 500 | Internal error |

---

# Logging

The module should log:

- Scan created
- Scan started
- Scan completed
- Scan failed
- Scanner invocation
- Status transitions
- Unexpected failures

Logs should include:

- Scan ID
- Target ID
- Timestamp
- Status

Sensitive information must never be logged.

---

# Dependencies

Depends on:

- Target Validation Module
- Scanner Engine
- Repository Layer
- PostgreSQL

Does not depend on:

- Risk Engine
- AI Engine
- Reporting Engine

---

# Testing Requirements

## Unit Tests

- Scan creation
- Status transitions
- Duplicate scan detection
- Invalid target handling
- Metadata updates

---

## Integration Tests

- Repository operations
- Database persistence
- Scanner Engine invocation
- Transaction rollback

---

## API Tests

- Create scan
- List scans
- Retrieve scan
- Invalid target
- Duplicate requests
- Status endpoint

All APIs must be validated using Postman.

---

# Future Enhancements

Future capabilities include:

- Scheduled scans
- Cron scheduling
- Distributed scan workers
- Queue management
- Priority-based execution
- Concurrent scan limits
- Retry policies
- Pause/Resume
- Scan cancellation
- Notification hooks
- WebSocket progress updates
- Message queue integration (RabbitMQ, Redis Streams, Kafka)

These enhancements should integrate without changing the existing REST API contracts.

---

# Definition of Done

The Scan Management module is complete only when:

- Scan lifecycle implemented
- CRUD APIs completed
- Status management implemented
- Database integration completed
- Scanner Engine integration completed
- Unit tests passing
- Integration tests passing
- API tests completed
- Documentation updated
- Repository committed according to project standards

Only after satisfying all criteria may development proceed to the Scanner Engine module.

---

# Related Documentation

- `modules_docs/01_target_validation.md`
- `architecture_docs/system_architecture.md`
- `architecture_docs/data_flow.md`
- `architecture_docs/database.md`
- `architecture_docs/security.md`
- `backend/backend.md`