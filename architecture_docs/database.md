# Database Architecture

**Project:** Automated Vulnerability Assessment Platform (AVAP)

**File:** `architecture_docs/database.md`

**Version:** 1.0

**Status:** Active

---

# Purpose

This document defines the database architecture of the Automated Vulnerability Assessment Platform (AVAP).

It specifies:

- Database design philosophy
- Entity relationships
- Data ownership
- Normalization rules
- Naming standards
- Integrity constraints
- Transaction boundaries
- Future extensibility

Implementation details are documented separately in:

- `backend/database.md`

---

# Database Goals

The database is designed to provide:

- Data integrity
- High consistency
- Scalability
- Auditability
- Maintainability
- Efficient querying
- Extensibility
- ACID compliance

The schema must support future enterprise capabilities without requiring major redesign.

---

# Database Technology

| Component | Technology |
|----------|------------|
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.x |
| Migration Tool | Alembic |

PostgreSQL is selected because it provides:

- ACID transactions
- Mature indexing
- JSON support
- Strong relational capabilities
- Excellent community support
- Long-term stability

---

# Database Design Principles

The database follows the principles below.

- Third Normal Form (3NF)
- Strong referential integrity
- Explicit foreign keys
- Minimal redundancy
- Immutable audit history where applicable
- Clear ownership of data
- Predictable naming
- Transactional consistency

---

# High-Level Database Architecture

```
                    Targets
                       │
                       │
                       ▼
                 Scan Jobs
                       │
         ┌─────────────┴─────────────┐
         ▼                           ▼
     Assets                  Vulnerabilities
         │                           │
         └─────────────┬─────────────┘
                       ▼
                Risk Assessments
                       │
                       ▼
               AI Recommendations
                       │
                       ▼
                    Reports

                Audit Logs
```

---

# Core Entities

The platform currently consists of the following logical entities.

| Entity | Responsibility |
|---------|---------------|
| Target | Stores scan targets |
| ScanJob | Represents a scan execution |
| Asset | Stores discovered assets |
| Vulnerability | Stores normalized findings |
| RiskAssessment | Stores calculated risk (explicit scope: vulnerability, asset, scan, or assessment) |
| AIRecommendation | Stores AI-generated remediation, identified by (risk_assessment_id, provider, model, prompt_version) |
| Report | Stores generated reports |
| AuditLog | Stores system events |

Additional entities may be introduced as the platform evolves.

---

# Entity Relationships

```
Target

1

↓

N

ScanJob

↓

1

↓

N

Asset

↓

1

↓

N

Vulnerability

↓

1

↓

1

RiskAssessment

↓

1

↓

1

AIRecommendation

↓

1

↓

N

Report
```

Audit logs remain independent and reference system events where applicable.

---

# Data Ownership

Each entity has a clearly defined owner.

| Entity | Owner |
|---------|------|
| Target | Target Validation Module |
| ScanJob | Scan Management Module |
| Asset | Asset Management Module |
| Vulnerability | Parser Engine |
| RiskAssessment | Risk Engine |
| AIRecommendation | AI Engine |
| Report | Reporting Engine |
| AuditLog | Audit Logging Module |

Business logic should only modify entities owned by the corresponding module.

---

# Data Lifecycle

The typical lifecycle is:

```
Target

↓

Scan Job

↓

Scanner

↓

Parsed Results

↓

Assets

↓

Vulnerabilities

↓

Risk Assessment

↓

AI Recommendation

↓

Report
```

Historical records should remain available unless explicitly archived or deleted.

---

# Naming Standards

## Tables

Plural, snake_case.

Examples:

```
targets

scan_jobs

assets

vulnerabilities

risk_assessments

reports
```

---

## Columns

snake_case.

Examples:

```
created_at

updated_at

scan_status

risk_score
```

---

## Primary Keys

Every table uses:

```
id
```

---

## Foreign Keys

Examples:

```
target_id

scan_job_id

asset_id

vulnerability_id
```

---

## Timestamp Columns

Every primary entity should include:

```
created_at

updated_at
```

Future soft-delete support may introduce:

```
deleted_at
```

---

# Normalization Strategy

The database follows Third Normal Form (3NF).

Objectives:

- Reduce duplication
- Preserve consistency
- Simplify maintenance

Denormalization should only occur after performance analysis.

---

# Constraints

The database should use:

- Primary Keys
- Foreign Keys
- Unique Constraints
- Check Constraints
- NOT NULL constraints
- Default values where appropriate

Business rules should not rely solely on database constraints.

---

# Indexing Strategy

Indexes should exist for:

- Foreign keys
- Frequently searched columns
- Scan status
- Hostnames
- IP addresses
- CVE identifiers
- Report identifiers

Composite indexes should be added only when supported by query analysis.

---

# Transaction Strategy

Transactions must be atomic.

Each business operation should either:

- Complete successfully
- Roll back completely

Examples:

- Create scan
- Store parsed results
- Generate report

Partial persistence should be avoided.

---

# Repository Ownership

Only repositories communicate with the database.

```
Service

↓

Repository

↓

Database
```

Services must never execute SQL directly.

---

# Data Integrity

Integrity is maintained through:

- Foreign keys
- Constraints
- Transactions
- Validation
- Repository abstraction

Application logic and database constraints complement each other.

---

# Historical Data

Historical scan data should be retained.

A new scan should create a new `ScanJob` while preserving previous executions for comparison and auditing.

Assets and vulnerabilities should support historical tracking where applicable.

---

# Future Scalability

The schema is designed to accommodate future features including:

- Authentication
- RBAC
- Multi-user support
- Multi-tenancy
- Scheduled scans
- Distributed scanners
- Compliance frameworks
- Cloud assets
- Threat intelligence
- Ticketing integrations

These additions should integrate without redesigning the existing core schema.

---

# Migration Strategy

Database schema changes must be managed using Alembic.

Guidelines:

- Every schema change requires a migration.
- Migrations should be version-controlled.
- Existing data must be preserved where possible.
- Breaking migrations require explicit review.

---

# Backup and Recovery

Although outside the current implementation scope, the architecture assumes:

- Regular database backups
- Point-in-time recovery
- Disaster recovery procedures
- Restore validation

The schema should support reliable recovery without data inconsistency.

---

# Security Considerations

The database should enforce:

- Least privilege access
- Parameterized queries (through SQLAlchemy)
- Secure credentials
- Encrypted connections in production
- Protection of sensitive configuration

Secrets must never be stored in application code.

---

# Future Enhancements

Potential future architectural enhancements include:

- Table partitioning for large scan datasets
- Read replicas for reporting workloads
- Full-text search
- Materialized views for dashboards
- Archival strategy for historical scans
- Time-series optimization for scan history
- Logical replication

These enhancements should build upon the current relational design without altering the logical data model.

---

# Related Documentation

- `system_architecture.md` — Overall system design
- `data_flow.md` — Data movement throughout the platform
- `security.md` — Security architecture
- `backend/database.md` — SQLAlchemy models, migrations, repository implementation, and database access patterns
- `modules_docs/` — Entity-specific behavior and module ownership