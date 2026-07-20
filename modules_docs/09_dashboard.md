

# Dashboard APIs Module

**Module:** 09 - Dashboard APIs

**File:** `modules_docs/09_dashboard.md`

**Version:** 1.0

**Status:** Implemented

---

# Purpose

The Dashboard APIs module is responsible for exposing aggregated, read-optimized security data for visualization and analytics.

Unlike other modules that create or modify security data, the Dashboard APIs module acts as a **read-only aggregation layer**, combining information from multiple modules into a unified representation suitable for dashboards, analytics, and future frontend applications.

The Dashboard APIs module does **not** own business data. It only consumes existing data and presents it efficiently.

---

# Objectives

The Dashboard APIs module is designed to:

* Provide aggregated security metrics
* Support dashboard visualizations
* Expose executive-level summaries
* Expose technical security metrics
* Minimize database queries through aggregation
* Support future frontend development
* Support future analytics and monitoring
* Provide scalable read APIs

---

# Responsibilities

The Dashboard APIs module is responsible for:

* Aggregating platform metrics
* Returning dashboard summaries
* Returning scan statistics
* Returning vulnerability statistics
* Returning asset statistics
* Returning risk summaries
* Returning report statistics
* Returning AI recommendation summaries

The module is **not responsible for**:

* Scanner execution
* Parsing scan results
* Asset management
* Risk calculation
* AI recommendation generation
* Report generation
* Database ownership

---

# Design Principles

The Dashboard APIs module follows:

* Read-Only Architecture
* Aggregation over Computation
* Separation of Concerns
* Optimized Queries
* Stateless APIs
* High Performance
* Extensibility

The module never modifies business data.

---

# High-Level Architecture

```text
                    Dashboard Client
                           │
                           ▼
                  Dashboard API Layer
                           │
                           ▼
                Dashboard Service Layer
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    Asset Repository   Risk Repository   Report Repository
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                Aggregation Engine
                           │
                           ▼
                 Dashboard Response
```

---

# Internal Components

| Component                  | Responsibility                     |
| -------------------------- | ---------------------------------- |
| Dashboard Coordinator      | Entry point for dashboard requests |
| Dashboard Service          | Orchestrates dashboard queries     |
| Metrics Aggregator         | Aggregates platform statistics     |
| Repository Layer           | Retrieves required data            |
| Dashboard Response Builder | Builds API response models         |

---

# Implemented Architecture and Scope

The implementation follows the documented layering exactly:

| Conceptual Component | Implementation |
|---|---|
| Dashboard Coordinator / Dashboard Service | `app/services/dashboard_service.py` (`DashboardService`) |
| Repository Layer / Metrics Aggregator | `app/repositories/dashboard_repository.py` (`DashboardRepository`), plus reuse of `RiskRepository.get_assessment()` and `ReportRepository.get_all()` |
| Dashboard Response Builder | `app/schemas/dashboard.py` (frozen Pydantic v2 read models) |
| Dashboard API Layer | `app/api/routes/v1/dashboard.py`, mounted at `/api/v1/dashboard` |

`DashboardRepository` performs every cross-domain aggregate query (`COUNT`,
`GROUP BY`, window-function ranking) directly in SQL. It never adds, updates,
deletes, flushes, or commits, and it never recalculates risk or severity —
it only reads what Modules 02/05/06/07/08 have already persisted. No new
database table, index, or Alembic migration was required: every dashboard
query runs against the existing schema using existing indexed columns
(`RiskAssessment.scope`, `.asset_id`, `.vulnerability_id`).

**Deviation from `backend/project_structure.md`'s illustrative `app/dashboard/`
sketch:** that document shows a dedicated `app/dashboard/{service.py,
aggregator.py}` package. This implementation places `DashboardService` in
`app/services/` and `DashboardRepository` in `app/repositories/` instead,
matching the actual convention every other completed module uses (Target,
Scan, Asset, Vulnerability, Risk, AI, and Report services/repositories all
live in the flat `app/services/`/`app/repositories/` directories; a
dedicated top-level package — `risk_engine/`, `ai/`, `reporting/` — is only
used where a module has substantial *pure, non-persistence* logic with no
existing single-repository home). Since SQL already performs the
aggregation directly inside `DashboardRepository`, a separate
`aggregator.py` pure-Python layer would be a redundant pass-through with no
independent responsibility. Tests likewise live in `tests/services/`,
`tests/repositories/`, and `tests/api/` rather than a new `tests/dashboard/`
directory, for the same reason.

## Metric Ownership Map

| Metric family | Authoritative source |
|---|---|
| Targets, scans, scan status/duration | `Target`, `ScanJob` |
| Assets, network services | `Asset`, `NetworkService` |
| Vulnerability identity and severity | `Vulnerability.severity_rating` (never `RiskAssessment`) |
| Scan findings (observations) | `ScanFinding` |
| Deterministic risk score/level/distribution | `RiskAssessment` (Module 06 only) |
| AI recommendation availability/freshness | `AIRecommendation` vs. `RiskAssessment.calculated_at` (Module 07's own freshness rule) |
| Report counts/formats/recency | `Report` metadata (Module 08); the filesystem is never inspected |

## Corrections to this document's original illustrative examples

Two originally-listed Asset Dashboard example metrics do not map to any
persisted field and are intentionally **not implemented**, per the
principle of never fabricating data to satisfy an example:

* **Active Assets** — `Asset` has no status/liveness column. There is no
  persisted concept of an asset being "active" vs. "inactive".
* **Assets by Type** — `Asset` has no type/classification column (only
  `ipv4`, `hostname`, `operating_system`).

Both are replaced by `total_network_services` (Service exposure, a real,
owned entity) and `recently_discovered_assets` (a real, persisted
`Asset.created_at`-ordered projection).

## "Current" per-entity risk semantics

`RiskAssessment` at ASSET and VULNERABILITY scope is recorded per
`(scan, entity)` pair — the same asset or vulnerability can have multiple
rows across different scans. There is no single "latest" row that is
unambiguously authoritative platform-wide. The dashboard therefore defines
an entity's **current risk** as the **maximum `risk_score` ever persisted**
for that entity across all scans (ties broken by the `RiskAssessment` row's
own id), mirroring Module 06's own "maximum of children" aggregation
philosophy rather than inventing a new "latest scan wins" rule. This
population is used for `risk_level_distribution`, `top_risk_assets`, and
`high_risk_asset_count`.

## Historical trends

The schema does not retain periodic snapshots of any metric (no
time-series/analytics table exists). Consistent with "do not fabricate
metrics," this implementation exposes only current-state aggregates and
bounded "recent N" projections (`recent_scans`, `recently_discovered_assets`,
`recent_reports`) ordered by real persisted timestamps. No 7-day/30-day
trend charts are computed by grouping current-state rows by `created_at`,
since that would misrepresent point-in-time inventory state as a time
series.

---

# Dashboard Categories

The Dashboard APIs expose multiple dashboard views.

## Executive Dashboard (`GET /dashboard/summary`)

Implemented fields (`DashboardSummaryResponse`):

* `total_targets`, `total_scans`, `total_assets` — direct table counts
* `unique_vulnerability_count` — distinct `Vulnerability` catalog identities
* `critical_vulnerability_count` — subset with `severity_rating == "Critical"`
* `total_reports_generated` — count of persisted `Report` rows
* `overall_risk_score`, `overall_risk_level` — the singleton ASSESSMENT-scope
  `RiskAssessment` (`0.0` / `INFORMATIONAL` when none has been calculated yet)
* `high_risk_asset_count` — assets whose current (worst) ASSET-scope risk
  level is `HIGH` or `CRITICAL`

An empty platform returns all-zero counts with HTTP 200, never 404.

---

## Operations metrics (folded into `GET /dashboard/scans`)

Running/Completed/Failed counts, Scan Success Rate, and Average Scan
Duration are all returned by the Scan Statistics endpoint below rather than
as a separate "Operations" endpoint, since they share the same `ScanJob`
query and the documented REST surface defines no separate `/operations`
route.

---

## Asset Dashboard (`GET /dashboard/assets`)

Implemented fields (`DashboardAssetStatisticsResponse`):

* `total_assets` — count of `Asset` rows
* `total_network_services` — count of `NetworkService` rows (service exposure)
* `recently_discovered_assets` — bounded (`limit`, default 10, max 50) list
  ordered by `Asset.created_at` descending

"Active Assets" and "Assets by Type" from this document's original example
list are not implemented; see "Corrections to this document's original
illustrative examples" above.

---

## Vulnerability Dashboard (`GET /dashboard/vulnerabilities`)

Implemented fields (`DashboardVulnerabilityStatisticsResponse`):

* `unique_vulnerability_count` — distinct `Vulnerability` catalog identities
* `finding_count` — total `ScanFinding` rows across all scans (deliberately
  a separate field: a finding count is never substituted for a vulnerability
  identity count, or vice versa)
* `severity_distribution` — `{critical, high, medium, low, informational,
  unknown}`, grouped by `Vulnerability.severity_rating`. `informational`
  captures the `"None"` rating; `unknown` captures any other persisted value,
  so unrecognized data can never inflate a known severity bucket.

---

## Risk Dashboard (`GET /dashboard/risk`)

Implemented fields (`DashboardRiskStatisticsResponse`), sourced exclusively
from Module 06 `RiskAssessment` rows — never from `Vulnerability.severity_rating`:

* `overall_risk_score`, `overall_risk_level` — the ASSESSMENT-scope singleton
* `risk_level_distribution` — count of assets per risk level, using each
  asset's current (worst) ASSET-scope risk (see "'Current' per-entity risk
  semantics" above)
* `top_risk_assets` — bounded (`top_limit`, default 10, max 50) list of
  assets ranked by current risk score descending, tie-broken by IPv4
  ascending
* `top_risk_vulnerabilities` — bounded (`top_limit`) list of vulnerability
  identities ranked by their current (worst) VULNERABILITY-scope risk score
  descending, tie-broken by name ascending; includes `affected_asset_count`
  (distinct assets carrying that vulnerability) as supplementary context,
  never as part of the ranking itself

---

## Reporting Dashboard (`GET /dashboard/reports`)

Implemented fields (`DashboardReportStatisticsResponse`), sourced only from
Module 08 `Report` metadata — the filesystem is never inspected:

* `total_reports_generated`, `reports_by_format`, `latest_report_generated_at`
* `recent_reports` — bounded (`limit`, default 10, max 50) list ordered by
  `generated_at` descending

---

## AI Dashboard (`GET /dashboard/ai`)

Implemented fields (`DashboardAIStatisticsResponse`):

* `total_recommendations`, `recommendations_by_provider`,
  `recommendations_by_model`, `recommendations_by_severity` (joined against
  the recommendation's own vulnerability's `severity_rating`)
* `eligible_vulnerability_risk_count` — every persisted VULNERABILITY-scope
  `RiskAssessment`
* `current_recommendation_count` — the subset with at least one
  `AIRecommendation` whose `generated_at >= risk_assessment.calculated_at`
  (Module 07's own freshness rule; evaluated read-only, never regenerated)
* `missing_recommendation_count` — `eligible - current`
* `remediation_coverage_percent` — `current / eligible * 100` rounded to one
  decimal, or `0.0` when `eligible == 0` (documented empty-state, never a
  division-by-zero error)

This reports recommendation **availability**, not remediation
effectiveness — the field is deliberately not named "AI effectiveness."
The dashboard never triggers AI generation.

---

# Data Sources

The Dashboard APIs consume information from:

* Target Validation
* Scan Management
* Asset & Vulnerability Management
* Risk Assessment
* AI Engine
* Reporting Engine

The module never communicates with:

* Scanner Engine
* Parser Engine

---

# Aggregation Workflow

```text
Dashboard Request

↓

Dashboard Service

↓

Repository Queries

↓

Metrics Aggregation

↓

Response Builder

↓

Dashboard Response
```

Business calculations are not performed during dashboard generation.

---

# REST APIs

Base endpoint:

```text
/api/v1/dashboard
```

---

## Executive Summary

```text
GET /dashboard/summary
```

Returns overall platform statistics. No query parameters.

---

## Asset Statistics

```text
GET /dashboard/assets?limit=10
```

Returns asset-related metrics. `limit` (recently discovered assets):
integer, default 10, min 1, max 50.

---

## Vulnerability Statistics

```text
GET /dashboard/vulnerabilities
```

Returns vulnerability metrics. No query parameters.

---

## Risk Statistics

```text
GET /dashboard/risk?top_limit=10
```

Returns aggregated risk information. `top_limit` (top-risk assets and
vulnerabilities): integer, default 10, min 1, max 50.

---

## Scan Statistics

```text
GET /dashboard/scans?limit=10
```

Returns scan execution statistics. `limit` (recent scans): integer,
default 10, min 1, max 50.

---

## Report Statistics

```text
GET /dashboard/reports?limit=10
```

Returns report-related metrics. `limit` (recent reports): integer,
default 10, min 1, max 50.

---

## AI Statistics

```text
GET /dashboard/ai
```

Returns AI recommendation metrics. No query parameters.

---

# Response Model

Every dashboard endpoint uses the platform's existing standardized
envelope (`app.api.responses.api_response.SuccessResponse`), consistent
with every other implemented module — not a bespoke dashboard-only
envelope. Each response's `data` payload includes its own `generated_at`
aggregation timestamp:

```json
{
    "success": true,
    "data": {
        "generated_at": "2026-07-12T10:00:00Z",
        "total_assets": 125,
        "unique_vulnerability_count": 648,
        "critical_vulnerability_count": 18,
        "overall_risk_level": "HIGH",
        "...": "..."
    },
    "error": null
}
```

The response model remains stable across frontend implementations.

---

# Data Flow

```text
Repositories

↓

Dashboard Service

↓

Metrics Aggregator

↓

Dashboard Response

↓

Client
```

Only aggregated information leaves the module.

---

# Performance Considerations

Dashboard APIs are expected to be read-heavy.

The module should:

* Minimize database round-trips
* Use optimized aggregate queries
* Avoid unnecessary joins
* Support pagination where applicable
* Support future caching
* Return lightweight responses

Future implementations may introduce Redis-based caching without changing the API contract.

---

# Security Requirements

The Dashboard APIs shall:

* Return only aggregated information
* Prevent exposure of internal implementation details
* Validate request parameters
* Support future authorization checks
* Avoid leaking sensitive infrastructure details

The module must never expose:

* Environment variables
* Credentials
* Internal file paths
* Scanner artifacts
* Raw parser output

---

# Error Handling

Possible failures include:

* Repository failure
* Invalid query parameters
* Aggregation failure
* Database connectivity issues

Errors should be returned using standardized API responses.

---

# Logging

The Dashboard APIs should log:

* Dashboard requests
* Response generation
* Aggregation duration
* Repository failures

Logs should include:

* Endpoint
* Processing Time
* Request Identifier (future)

Sensitive data must never be logged.

---

# Dependencies

Depends on:

* Repository Layer
* Asset & Vulnerability Management
* Risk Assessment
* AI Engine
* Reporting Engine

Does not depend on:

* Scanner Engine
* Parser Engine

---

# Future Enhancements

The architecture supports:

* Real-time dashboards
* WebSocket updates
* Time-series analytics
* Historical trends
* Compliance dashboards
* Multi-tenant dashboards
* Custom widgets
* Saved dashboard layouts
* Grafana integration
* Prometheus metrics
* Business Intelligence integrations

These enhancements should integrate without modifying existing API contracts.

---

# Testing Requirements

## Repository Tests (`tests/repositories/test_dashboard_repository.py`, 16 tests)

Empty-database aggregates, total counts, scan status grouping, vulnerability
severity grouping (including an unrecognized "unknown" value), asset
risk-level distribution scoped to the worst-per-asset population, top-risk
asset ranking with deterministic tie-breaking, top-risk vulnerability
ranking plus affected-asset counts, report format/latest-timestamp
aggregation, AI recommendation grouping by provider/model/severity,
freshness-based remediation coverage (current vs. stale vs. missing), and a
structural check that no dashboard query adds/dirties session state.

## Service Tests (`tests/services/test_dashboard_service.py`, 17 tests)

Empty-state responses for all seven endpoints; authoritative-source
separation (severity from `Vulnerability`, never from `RiskAssessment`;
asset risk vs. vulnerability risk never conflated); worst-per-asset
high-risk counting; stale-recommendation exclusion; zero-denominator
coverage; report statistics sourced from metadata; recent-scan projections
using real persisted `started_at`/`completed_at`/`execution_duration`
fields; terminal-scan-only success rate; deterministic repeated responses
for identical persisted state.

## Schema Tests (`tests/services/test_dashboard_schemas.py`, 10 tests)

Valid and empty-state construction, negative count rejection, risk score
bounds (0.0–10.0) rejection, invalid enum rejection, invalid UUID
rejection, invalid datetime rejection.

## API Tests (`tests/api/test_dashboard_api.py`, 21 tests)

All seven endpoints return HTTP 200 (never 404) on an empty database and
reflect persisted state once populated; `limit`/`top_limit` bounds
(minimum, maximum, non-numeric) rejected with 422; no internal path,
credential, or configuration exposure in any response body; POST rejected
with 405 on GET-only routes; dashboard reads never create data.

## Integration Test (`tests/services/test_dashboard_integration.py`, 1 test)

A single end-to-end flow exercising the real repository/service/API
boundaries (`DashboardService` is never mocked): Module 05 findings across
two distinct vulnerability identities → Module 06 risk calculation →
Module 07 one current and one deliberately stale AI recommendation →
Module 08 report generation via the real REST API → all seven Module 09
dashboard endpoints, asserting vulnerability-identity counts, finding
counts, severity distribution, risk distribution, top-risk rankings,
freshness-based coverage, and report/scan/asset statistics all match the
seeded, deliberately non-uniform data.

All APIs are directly testable via the existing FastAPI `TestClient`-backed
suite above; no separate Postman collection artifact was produced for this
increment.

---

# Definition of Done

The Dashboard APIs module is complete:

* Dashboard Service implemented (`app/services/dashboard_service.py`)
* Dashboard Repository implemented (`app/repositories/dashboard_repository.py`)
* Response models implemented (`app/schemas/dashboard.py`)
* REST APIs completed — all seven documented endpoints
* Aggregation occurs in SQL (`COUNT`, `GROUP BY`, window-function ranking);
  no full-table Python counting, no N+1 query pattern
* 65 new tests added (16 repository + 17 service + 10 schema + 21 API + 1
  integration); complete backend regression: 449 passed, 0 failed
  (384-test baseline + 65), verified on Python 3.12.13 and 3.14.6
* Documentation updated (this file)

---

# Related Documentation

* `modules_docs/08_reporting.md`
* `architecture_docs/system_architecture.md`
* `architecture_docs/data_flow.md`
* `architecture_docs/database.md`
* `architecture_docs/security.md`
* `architecture_docs/development_standards.md`
* `backend/backend.md`
