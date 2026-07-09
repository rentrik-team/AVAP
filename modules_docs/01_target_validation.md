# Target Validation Module

**Module:** 01 - Target Validation

**File:** `modules_docs/01_target_validation.md`

**Version:** 1.0

**Status:** Planned

---

# Purpose

The Target Validation module is responsible for validating, normalizing, and registering scan targets before they enter the vulnerability assessment pipeline.

It serves as the first security boundary of the platform by ensuring that only valid, supported, and authorized targets are accepted for scanning.

No scan may begin unless the target successfully passes this module.

---

# Module Responsibilities

The Target Validation module is responsible for:

- Validating scan targets
- Normalizing target information
- Preventing duplicate targets
- Classifying target types
- Storing validated targets
- Providing CRUD APIs for targets
- Supplying validated targets to the Scan Management module

The module **does not**:

- Execute scanners
- Perform DNS enumeration
- Discover services
- Calculate risk
- Generate reports

---

# Supported Target Types

The module currently supports:

| Target Type | Example |
|--------------|---------|
| IPv4 Address | `192.168.1.10` |
| IPv4 CIDR | `192.168.1.0/24` |
| Hostname | `example.com` |

Future support may include:

- IPv6
- URL-based scanning
- Cloud assets
- AWS resources
- Azure resources
- GCP resources

---

# Validation Rules

Every incoming target must satisfy the following validation rules.

## IPv4 Address

Requirements:

- Valid IPv4 format
- No malformed octets
- No invalid characters
- RFC-compliant address

Validation performed using Python's `ipaddress` standard library.

---

## CIDR Range

Requirements:

- Valid CIDR notation
- Valid subnet mask
- Supported prefix length

CIDR validation uses the Python standard library.

---

## Hostname

Requirements:

- RFC-compliant hostname
- Valid length
- Valid labels
- No illegal characters

Hostname resolution is **not** performed during validation.

---

# Normalization

Before persistence, all targets are normalized.

Examples:

Input:

```
Example.COM
```

Stored:

```
example.com
```

Whitespace should be removed.

Duplicate formatting differences should be eliminated.

---

# Duplicate Detection

Before storing a target, the module checks for existing records.

Duplicate determination is based on normalized values.

Duplicate targets are rejected with an appropriate error response.

---

# Business Rules

The module enforces the following rules:

- Every target must have a unique normalized value.
- Unsupported target formats are rejected.
- Empty targets are rejected.
- Invalid targets are rejected.
- Duplicate targets are rejected.
- Only validated targets are persisted.

---

# Module Workflow

```
Client

↓

POST /targets

↓

Request Validation

↓

Target Type Detection

↓

Format Validation

↓

Normalization

↓

Duplicate Detection

↓

Persistence

↓

Response
```

---

# REST API

Base endpoint:

```
/api/v1/targets
```

---

## Create Target

```
POST /targets
```

Creates a new scan target.

---

## Get All Targets

```
GET /targets
```

Returns all registered targets.

Supports future pagination.

---

## Get Target

```
GET /targets/{target_id}
```

Returns a single target.

---

## Update Target

```
PUT /targets/{target_id}
```

Updates an existing target.

Target validation is performed again before persistence.

---

## Delete Target

```
DELETE /targets/{target_id}
```

Removes a target.

Deletion should not remove historical scan records.

---

# Request Model

Example:

```json
{
  "target": "192.168.1.10"
}
```

Future fields may include:

- description
- tags
- owner
- criticality

---

# Response Model

Example:

```json
{
  "id": 1,
  "target": "192.168.1.10",
  "target_type": "IPv4",
  "created_at": "...",
  "updated_at": "..."
}
```

---

# Database Ownership

Primary entity:

```
Target
```

Primary table:

```
targets
```

The module owns all CRUD operations on this entity.

---

# Dependencies

The module depends on:

- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL

Python Standard Library:

- `ipaddress`
- `re`
- `uuid`

No third-party validation libraries should be introduced unless justified.

---

# Security Requirements

The module shall:

- Validate every request.
- Reject malformed input.
- Reject invalid IP addresses.
- Reject invalid CIDR ranges.
- Reject invalid hostnames.
- Reject duplicate entries.
- Prevent SQL Injection through ORM usage.
- Prevent command injection by treating targets as data only.

No scanner execution occurs in this module.

---

# Error Handling

Possible errors include:

| HTTP Status | Description |
|--------------|-------------|
| 400 | Invalid target format |
| 404 | Target not found |
| 409 | Duplicate target |
| 422 | Validation failed |
| 500 | Internal server error |

Error responses should follow the platform's standard response format.

---

# Logging

The module should log:

- Target creation
- Target update
- Target deletion
- Validation failures
- Duplicate detection
- Unexpected errors

Sensitive information must never be logged.

---

# Testing Requirements

The module must include:

## Unit Tests

- IPv4 validation
- CIDR validation
- Hostname validation
- Normalization
- Duplicate detection

---

## Integration Tests

- Database persistence
- Repository operations
- API endpoints

---

## API Tests

- Create target
- Retrieve targets
- Update target
- Delete target
- Invalid requests
- Duplicate requests

All APIs must be verified using Postman before proceeding to the next module.

---

# Future Enhancements

Future versions may support:

- IPv6 validation
- URL targets
- Domain ownership verification
- DNS resolution
- Asset grouping
- Tags
- Labels
- Bulk target import
- CSV import
- Network discovery seeds
- Authentication integration
- RBAC restrictions

These enhancements should integrate without altering the existing API contract.

---

# Definition of Done

The Target Validation module is complete only when:

- Validation implemented
- Normalization implemented
- Duplicate detection implemented
- CRUD APIs completed
- Database integration completed
- Unit tests passing
- Integration tests passing
- API tests completed
- Documentation updated
- Git commit created according to the repository standards

Only after meeting all criteria may development proceed to the Scan Management module.

---

# Related Documentation

- `architecture_docs/system_architecture.md`
- `architecture_docs/data_flow.md`
- `architecture_docs/database.md`
- `architecture_docs/security.md`
- `architecture_docs/development_standards.md`
- `backend/backend.md`