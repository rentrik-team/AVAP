# Risk Assessment Module

**Module:** 06 - Risk Assessment

**File:** `modules_docs/06_risk_assessment.md`

**Version:** 1.0

**Status:** Implemented

---

# Purpose

The Risk Assessment module is responsible for transforming normalized vulnerabilities into deterministic, prioritized security risks.

It evaluates each vulnerability using predefined rules and contextual information to calculate a consistent and explainable risk score.

This module serves as the authoritative source of risk evaluation within the platform.

Unlike the AI Engine, which provides advisory recommendations, the Risk Assessment module produces deterministic results that are reproducible and auditable.

---

# Objectives

The module is designed to:

* Calculate deterministic risk scores
* Prioritize vulnerabilities
* Categorize security risks
* Aggregate risk at asset and scan levels
* Maintain auditability
* Provide standardized risk models
* Supply risk data to downstream modules

---

# Responsibilities

The Risk Assessment module is responsible for:

* Receiving normalized Assessment Packages
* Evaluating vulnerabilities
* Applying deterministic scoring rules
* Mapping severity levels
* Calculating asset risk
* Calculating scan risk
* Aggregating overall assessment risk
* Persisting calculated risk
* Providing risk APIs

The module is **not responsible for**:

* Executing scanners
* Parsing scanner output
* Storing vulnerabilities
* Generating remediation
* AI analysis
* Report generation

---

# Design Principles

The module follows:

* Deterministic Processing
* Explainable Results
* Rule-Based Evaluation
* Repeatable Calculations
* Separation of Concerns
* Single Responsibility Principle
* Auditability

Every execution with identical inputs must produce identical outputs.

---

# High-Level Architecture

```text
         Asset & Vulnerability Management
                     │
                     ▼
            Assessment Package
                     │
                     ▼
              Risk Coordinator
                     │
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
 Severity Engine  Context Engine  Rule Engine
      │              │              │
      └──────────────┼──────────────┘
                     ▼
          Risk Calculation Engine
                     │
                     ▼
         Risk Aggregation Engine
                     │
                     ▼
             Risk Assessment
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
      AI Engine        Reporting Engine
```

---

# Internal Components

| Component               | Responsibility                           |
| ----------------------- | ---------------------------------------- |
| Risk Coordinator        | Entry point of the module                |
| Severity Engine         | Standardizes vulnerability severity      |
| Context Engine          | Collects contextual information          |
| Rule Engine             | Applies deterministic scoring rules      |
| Risk Calculation Engine | Calculates individual risk scores        |
| Risk Aggregation Engine | Calculates asset, scan, and overall risk |
| Repository Layer        | Persists risk assessments                |

---

# Processing Workflow

```text
Assessment Package

↓

Extract Vulnerabilities

↓

Normalize Severity

↓

Apply Risk Rules

↓

Calculate Risk

↓

Aggregate Results

↓

Persist Risk

↓

Forward Results
```

---

# Risk Levels

The platform uses standardized risk categories.

| Level         | Description                    |
| ------------- | ------------------------------ |
| Informational | No immediate security impact   |
| Low           | Minor security concern         |
| Medium        | Moderate security risk         |
| High          | Significant security risk      |
| Critical      | Immediate remediation required |

These categories remain consistent across all scanners.

---

# Risk Calculation

Risk calculations are deterministic and implemented in `app/risk_engine/`.

Current evaluation considers:

* Scanner severity (`Vulnerability.severity_rating`)
* CVSS score, when available (`Vulnerability.severity_score`)
* Number of affected assets (within the calculation scope)
* Number of affected services (within the calculation scope)

Future versions may additionally consider:

* Asset criticality
* Exploit availability
* Threat intelligence
* Business impact
* Exposure duration
* Environmental score

The architecture allows these enhancements without changing module boundaries.

---

# Implemented Deterministic Methodology

All constants below are centralized in `app/risk_engine/rules.py`. Nothing in
this methodology is duplicated elsewhere.

## Calculation Version

```text
CALCULATION_VERSION = "1.0.0"
```

Persisted on every risk record. A rule change that alters numeric outcomes
must bump this version.

## Score Bounds

Every score is bounded `0.0` – `10.0` (matches CVSS range).

## 1. Base Score Selection / CVSS Handling / Missing CVSS Fallback

A vulnerability's `severity_score` (CVSS, 0.0–10.0) is used directly as the
base score whenever it is non-zero ("CVSS available"). When `severity_score`
is `0.0` (no CVSS provided by the scanner), the engine falls back to a
severity-rating mapping:

| Severity Rating | Fallback Base Score |
|------------------|---------------------|
| None             | 0.0                 |
| Low              | 2.5                 |
| Medium           | 5.5                 |
| High             | 8.0                 |
| Critical         | 9.5                 |

An unrecognized rating defensively falls back to the `None` value (`0.0`);
this is unreachable in practice because `ParsedVulnerability` already
validates the rating against this exact set at ingestion (Module 04/05).

## 2. Affected Asset / Service Influence

A vulnerability observed on more assets or services within the same scan
represents wider exposure and receives a small, bounded score bonus:

```text
asset_influence_bonus   = min((affected_asset_count   - 1) * 0.10, 1.0)
service_influence_bonus = min((affected_service_count - 1) * 0.05, 0.5)
```

`affected_asset_count` / `affected_service_count` are the number of distinct
assets/services in the scan carrying the same `vulnerability_id`.

## 3. Vulnerability Risk Calculation

```text
final_score = clamp(base_score + asset_influence_bonus + service_influence_bonus, 0.0, 10.0)
```

Computed once per `ScanFinding` that has a `vulnerability_id` (findings that
only record an open service, with no vulnerability, carry no risk).

## 4. Risk-Level Thresholds

Mirrors the CVSS bands already used by `OpenVASParser` for consistency:

| Score Range      | Risk Level    |
|------------------|---------------|
| `score >= 9.0`    | Critical      |
| `7.0 <= score < 9.0` | High       |
| `4.0 <= score < 7.0` | Medium     |
| `0.0 < score < 4.0`  | Low        |
| `score <= 0.0`       | Informational |

## 5. Asset Risk Aggregation

An asset's risk within a scan is the **maximum** score among its own
vulnerability-risk results in that scan (worst-case drives the aggregate).

## 6. Scan Risk Aggregation

A scan's risk is the maximum score among its asset-risk results.

## 7. Assessment Risk Aggregation

The overall, system-wide assessment risk is the maximum score among **all**
persisted scan-risk records (across every scan ever calculated). It is
recomputed as part of every scan calculation.

## Why "maximum" at every level

A single, uniform aggregation rule ("a scope is only as safe as its riskiest
component") is used at every level instead of a bespoke formula per level.
This keeps the methodology simple, fully deterministic, and trivially
explainable — the `supporting_factors` of every aggregated record name the
exact contributing entity that produced the score.

---

# Rule Engine

The Rule Engine applies configurable evaluation rules.

Examples:

* Severity normalization
* CVSS mapping
* Confidence adjustment
* Duplicate suppression
* Risk categorization

Business rules must remain version-controlled and deterministic.

---

# Context Engine

The Context Engine enriches calculations using locally available data.

Current context:

* Asset information
* Service information
* Vulnerability metadata
* Scan metadata

Future context:

* Asset ownership
* Business unit
* Critical infrastructure
* Compliance scope
* Threat intelligence

External services are not required for current implementation.

---

# Risk Aggregation

The module calculates risk at multiple levels.

## Vulnerability Risk

Individual risk score for each vulnerability.

---

## Asset Risk

Overall risk of an asset based on all associated vulnerabilities.

---

## Scan Risk

Overall risk produced by a single scan.

---

## Assessment Risk

Overall risk representing the complete assessment.

---

# Data Model

The `RiskAssessment` entity (`app/models/risk_assessment.py`) contains:

* Risk Identifier (`id`)
* Explicit Scope (`scope`: `VULNERABILITY` / `ASSET` / `SCAN` / `ASSESSMENT`)
* Risk Score (`risk_score`, bounded 0.0–10.0)
* Risk Level (`risk_level`)
* Calculation Version (`calculation_version`)
* Calculation Timestamp (`calculated_at`)
* Supporting Factors (`supporting_factors`, JSONB — the exact deterministic
  inputs that produced the score, e.g. `base_score`, `cvss_used`,
  `affected_asset_count`, `aggregation_method`, `contributing_entity_id`)
* Scope-dependent associations (`scan_id`, `asset_id`, `vulnerability_id`,
  `service_id`)

Scope is never inferred from which foreign keys happen to be populated. A
database `CHECK` constraint (`chk_risk_assessment_scope_invariants`) enforces
the exact required/forbidden association per scope, and five partial unique
indexes guarantee at most one authoritative row per scope/entity combination
(recalculation updates that row in place).

Future fields may include:

* Business Impact
* Threat Score
* Environmental Score

---

# Database Ownership

Primary table:

```text
risk_assessments
```

Associated relationships:

* assets
* vulnerabilities
* services
* scan_jobs

The module owns only calculated risk records. See
`architecture_docs/database.md` and Alembic revision `0004_risk_assessment`
for the full schema.

---

# Idempotency and Recalculation

`RiskService.calculate_risk_for_scan` is safe to call repeatedly:

* **First calculation** — inserts one row per scope/entity combination.
* **Repeated calculation, unchanged inputs** — recomputes identical values
  and updates the existing rows in place (verified by the persisted
  `id` remaining unchanged); no duplicate rows are created.
* **Recalculation after finding changes** — updates the existing rows with
  the new deterministic result.
* **Partial failure** — the whole calculation runs in one transaction owned
  by `RiskService`. Any exception rolls back every write from that attempt;
  no partially calculated risk state (e.g. vulnerability rows without their
  asset/scan rollup) is ever left behind.
* **Concurrent/duplicate writes** — the partial unique indexes on
  `risk_assessments` are the actual source of truth for uniqueness, not the
  application's read-then-write logic.

---

# REST APIs

Base endpoint:

```text
/api/v1/risk
```

---

## Retrieve Risk Assessments

```text
GET /risk
```

Query parameters: `skip`, `limit`, `scope`, `risk_level`.

---

## Retrieve Risk by Asset

```text
GET /risk/assets/{asset_id}
```

Returns the paginated `ASSET`-scope risk history for one asset (404 if the
asset does not exist).

---

## Retrieve Risk by Scan

```text
GET /risk/scans/{scan_id}
```

Returns the `SCAN`-scope risk record (404 if the scan does not exist, or if
risk has not yet been calculated for it).

---

## Calculate Risk for a Scan

```text
POST /risk/scans/{scan_id}/calculate
```

Triggers deterministic risk calculation for a scan's persisted findings.
This endpoint is the explicit trigger the module doc's processing workflow
depends on: Module 06 does not automatically hook into `InventoryService`,
since doing so would require modifying the already-completed Module 05
pipeline. Safe to call repeatedly (idempotent recalculation, see below).

---

## Retrieve Overall Assessment

```text
GET /risk/summary
```

Returns the singleton `ASSESSMENT`-scope record (404 if no scan has been
calculated yet).

Future endpoints may include:

* Risk trends
* Historical comparisons
* Dashboard summaries

---

# Data Flow

```text
Assessment Package

↓

Risk Assessment

↓

Risk Records

↓

AI Engine

↓

Reporting Engine
```

Only deterministic risk information is forwarded.

---

# Security Requirements

The module shall:

* Operate only on normalized data
* Prevent unauthorized score modification
* Preserve calculation history
* Record calculation version
* Validate all input

The module must never:

* Execute scanners
* Consume raw scanner output
* Accept AI-generated risk scores

---

# Error Handling

Possible failures include:

* Missing assessment data
* Invalid vulnerability reference
* Calculation rule failure
* Repository failure
* Aggregation failure

Errors should be returned using structured exceptions.

---

# Logging

The module should log:

* Risk calculation started
* Risk calculation completed
* Aggregation completed
* Calculation failures
* Repository updates

Logs should include:

* Scan ID
* Asset Count
* Vulnerability Count
* Processing Time
* Calculation Version

Risk values may be logged; sensitive infrastructure details must not.

---

# Dependencies

Depends on:

* Asset & Vulnerability Management
* Repository Layer

Communicates with:

* AI Engine
* Reporting Engine

Does not communicate with:

* Scanner Engine
* Parser Engine

---

# Performance Considerations

The module should:

* Batch calculations where practical
* Avoid duplicate calculations
* Cache reusable metadata
* Minimize database writes

Optimizations must preserve deterministic results.

---

# Future Enhancements

The architecture supports:

* Environmental scoring
* CVSS v4 support
* EPSS integration
* Threat intelligence feeds
* Asset criticality weighting
* Compliance-aware scoring
* Machine-learning-assisted prioritization (advisory only)
* Historical risk trending
* Executive risk dashboards

These enhancements should extend the Rule Engine without modifying downstream modules.

---

# AI Integration

The Risk Assessment module provides structured risk data to the AI Engine.

The AI Engine may:

* Explain calculated risk
* Recommend remediation
* Prioritize remediation

The AI Engine must never:

* Modify calculated scores
* Change risk levels
* Override deterministic rules

Risk Assessment remains the single source of truth.

---

# Testing Requirements

Implemented in `backend/tests/risk/`, `backend/tests/repositories/test_risk_repository.py`,
`backend/tests/services/test_risk_service.py`, `backend/tests/services/test_risk_integration.py`,
and `backend/tests/api/test_risk_api.py` (85 tests total).

## Unit Tests (`tests/risk/`)

* Rule Engine: CVSS handling, missing-CVSS fallback, every severity mapping,
  score bounds, exact risk-level threshold boundaries, asset/service
  influence scaling and caps
* Context Engine: distinct asset/service counting, null-service handling
* Risk Calculator: deterministic scoring, bonus application, clamping
* Risk Aggregator: empty/single/multiple contributions, maximum rule
* Risk Coordinator: end-to-end per-scan calculation composition

---

## Persistence Tests (`tests/repositories/test_risk_repository.py`)

* First calculation, in-place update on recalculation
* CHECK constraint rejects invalid scope/entity combinations
* Partial unique index rejects duplicate scope/entity rows
* Repository flushes but never commits

---

## Service / Integration Tests (`tests/services/`)

* Empty findings, single finding, multiple assets
* Idempotent recalculation, recalculation after finding changes
* Assessment-level aggregation across multiple scans
* Transaction rollback leaves no partial risk state
* Module 05 → Module 06 → API end-to-end flow using real `InventoryService`
  processing followed by `RiskService` calculation and API retrieval

---

## API Tests (`tests/api/test_risk_api.py`)

* List, asset risk, scan risk, summary, calculation trigger
* Invalid UUID, missing asset/scan, not-yet-calculated scan
* Pagination, scope filtering, empty database

All endpoints are directly testable using Postman against
`http://localhost:8000/api/v1/risk`.

---

# Definition of Done

The Risk Assessment module is complete only when:

* [x] Rule Engine implemented (`app/risk_engine/rules.py`)
* [x] Severity Engine implemented (severity mapping within `rules.py`)
* [x] Context Engine implemented (`app/risk_engine/context.py`)
* [x] Risk Calculation Engine implemented (`app/risk_engine/calculator.py`)
* [x] Risk Aggregation implemented (`app/risk_engine/aggregator.py`, `coordinator.py`)
* [x] Database persistence completed (`risk_assessments` table, migration `0004`)
* [x] REST APIs completed (`/api/v1/risk/*`)
* [x] Unit tests passing
* [x] Integration tests passing
* [x] API tests completed
* [x] Documentation updated
* [x] Git commit created according to project standards

Only after meeting all criteria may development proceed to the AI Engine module.

---

# Related Documentation

* `modules_docs/05_asset_vulnerability_management.md`
* `architecture_docs/system_architecture.md`
* `architecture_docs/data_flow.md`
* `architecture_docs/database.md`
* `architecture_docs/security.md`
* `architecture_docs/development_standards.md`
* `backend/backend.md`
