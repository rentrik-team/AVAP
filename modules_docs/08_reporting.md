# Reporting Engine Module

**Module:** 08 - Reporting Engine

**File:** `modules_docs/08_reporting.md`

**Version:** 1.0

**Status:** Implemented

---
 
# Purpose

The Reporting Engine is responsible for generating professional, standardized, and portable security assessment reports from deterministic risk assessments and AI-assisted remediation recommendations.

The Reporting Engine serves as the final stage of the assessment pipeline by transforming normalized assessment data into structured reports suitable for technical teams, management, auditors, and clients.

The Reporting Engine **does not perform analysis**. It only presents information that has already been processed and validated by upstream modules.

---

# Objectives

The Reporting Engine is designed to:

* Generate professional vulnerability assessment reports
* Present deterministic risk assessments
* Include AI-assisted remediation guidance
* Produce standardized report formats
* Maintain report consistency
* Support multiple export formats
* Preserve report history
* Support future customization

---

# Responsibilities

The Reporting Engine is responsible for:

* Receiving finalized assessment data
* Building report models
* Applying report templates
* Generating PDF reports
<!-- * Generating JSON exports -->
* Generating HTML reports (Future)
* Generating CSV exports (Future)
* Storing report metadata
* Providing report download APIs

The Reporting Engine is **not responsible for**:

* Executing scanners
* Parsing scan results
* Calculating risk
* Generating AI recommendations
* Modifying assessment data

---

# Design Principles

The Reporting Engine follows:

* Template-Based Rendering
* Separation of Presentation and Data
* Deterministic Output
* Reusable Components
* Export Format Independence
* Immutable Reports
* Consistent Layout

Reports should remain reproducible for identical assessment data.

---

# High-Level Architecture

```text
             Risk Assessment
                    │
                    ▼
               AI Engine
                    │
                    ▼
        Report Data Aggregator
                    │
                    ▼
          Report Model Builder
                    │
                    ▼
          Report Template Engine
                    │
       ┌────────────┼─────────────┐
       ▼            ▼             ▼
 PDF Generator                HTML Generator (Future)
       │            │             │
       └────────────┼─────────────┘
                    ▼
           Report Repository
                    │
                    ▼
            Report Download API
```

---

# Internal Components

| Component              | Responsibility                      |
| ---------------------- | ----------------------------------- |
| Report Coordinator     | Entry point of the Reporting Engine |
| Report Data Aggregator | Collects all assessment data        |
| Report Model Builder   | Creates report domain models        |
| Template Engine        | Applies report templates            |
| PDF Generator          | Generates PDF reports               |
<!-- | JSON Exporter          | Produces JSON reports               | -->
| Report Repository      | Stores report metadata              |
| Download Service       | Serves generated reports            |

---

# Implemented Architecture and Scope

The initial implementation generates one report **per scan** (`scan_id`),
matching the Report Metadata fields already documented below (Report ID,
Scan ID, Target ID, Generation Timestamp). "Assessment"-level or
multi-scan report scopes are not implemented and are not invented.

The conceptual components map onto concrete modules as follows
(`backend/app/reporting/`, mirroring the frozen `backend/project_structure.md`
layout):

| Conceptual Component | Implementation |
|---|---|
| Report Coordinator | `app/services/report_service.py` (`ReportService`) |
| Report Data Aggregator / Report Model Builder | `app/reporting/generator.py` (`build_report_data`) |
| Template Engine | `app/reporting/templates.py` (ReportLab PlaJSONtypus styles, safe-text escaping) |
| PDF Generator | `app/reporting/pdf.py` (`render_pdf`) |
| Report Repository | `app/repositories/report_repository.py` |
| Download Service | `GET /reports/{report_id}/download` (FastAPI `FileResponse`) |

**PDF only for this increment.**  export is not implemented yet,
consistent with "if the documentation only requires PDF now, implement PDF
now." The `ReportData` contract (`app/schemas/report.py`) is already fully
format-neutral and Pydantic-serializable — a future JSON exporter can reuse
it (e.g. via `.model_dump_json()`) without any change to data assembly.
`Report.format` is a plain string (default `"PDF"`) specifically so adding
a format later requires no schema migration.

---

# Report Generation Workflow

```text
Assessment Complete

↓

Retrieve Risk Assessment

↓

Retrieve AI Recommendation

↓

Aggregate Data

↓

Build Report Model

↓

Apply Template

↓

Generate Report

↓

Store Report Metadata

↓

Return Report Reference
```

---

# Report Sources

The Reporting Engine consumes data from:

* Target Validation
* Scan Management
* Asset & Vulnerability Management
* Risk Assessment
* AI Engine

The Reporting Engine must never communicate directly with:

* Scanner Engine
* Parser Engine

---

# Report Model

The Report Model represents the complete assessment.

Typical sections include:

* Report Metadata
* Executive Summary
* Target Information
* Scan Summary
* Asset Inventory
* Vulnerability Summary
* Risk Assessment
* AI Recommendations
* Technical Findings
* Appendices

The Report Model is independent of any export format.

---

# Report Templates

Templates define presentation only.

They must not contain:

* Business logic
* Risk calculations
* AI processing

Templates should support:

* Branding (Future)
* Themes (Future)
* Localization (Future)

---

# PDF Generation

The initial implementation uses:

* ReportLab

Responsibilities:

* Professional layout
* Pagination
* Tables
* Headers
* Footers
* Cover page
* Table of contents (Future)

PDF generation must be deterministic.

---

<!-- # JSON Export

JSON exports provide machine-readable assessment data.

Use cases include:

* API integrations
* SIEM ingestion
* Automation
* Third-party tools

The JSON schema should remain versioned.

--- -->

# Future Export Formats

Future formats include:

* HTML
* CSV
* DOCX
* XML

Adding new formats should require implementing a new exporter without modifying existing report logic.

---

# Report Metadata

Implemented fields on the `reports` table (`app/models/report.py`):

* Report ID (`id`)
* Scan ID (`scan_id`, FK; target is reachable via `scan_job.target`, not
  duplicated onto `reports`)
* Generation Timestamp (`generated_at`)
* Export Format (`format`, currently always `"PDF"`)
* Report Template Version (`report_template_version`) — the "Generator
  Version" concept from this doc's original field list
* Risk Calculation Version (`risk_calculation_version`) — snapshot of the
  Module 06 `calculation_version` in effect at generation time
* Source Risk Calculated At (`source_risk_calculated_at`) — snapshot of the
  scan's SCAN-scope `RiskAssessment.calculated_at`; the point-in-time
  freshness anchor (see below)
* Overall Risk Score / Level (`overall_risk_score`, `overall_risk_level`)
* Vulnerability Count (`vulnerability_count`)
* AI Recommendations Included (`ai_recommendations_included`) — count of
  findings for which current advisory guidance was included, for auditability

---

# Point-in-Time Consistency

A report must represent one coherent assessment state, never a mix of
findings from one scan state and risk from another. This is achieved by
building a single immutable `ReportData` (`app/schemas/report.py`) from one
in-memory pass over the required repositories, and rendering the PDF from
that object alone — the renderer never queries the database.

Findings and assets are deterministically ordered (by IP address / name,
not by database row order) so that identical persisted state always
produces byte-for-byte identical report *content* across repeated
generations.

---

# AI Recommendation Freshness

A finding's advisory remediation guidance is included only when a current
`AIRecommendation` exists for that finding's own `VULNERABILITY`-scope
`RiskAssessment` — evaluated with the exact same rule Module 07 itself uses
(`recommendation.generated_at >= risk_assessment.calculated_at`). A stale
recommendation (generated before the most recent risk recalculation) is
never presented as current; the finding instead states that AI-assisted
remediation guidance is not currently available. The Reporting Engine never
calls the AI provider and never triggers regeneration — it only reads
whatever Module 07 has already produced.

---

# Report Identity and Regeneration

Reports are immutable, versioned artifacts, not "current state" resources
like `RiskAssessment` or `AIRecommendation`. Every successful
`POST /reports` call creates a **new** row and a **new** PDF file; existing
reports for the same scan are never overwritten, updated in place, or
deleted as a side effect of generating a new one. This preserves complete
report history, per this document's own "Immutable Reports" and "Preserve
report history" principles.

* **First generation** — inserts a new report row and file.
* **Repeated generation** — inserts another new report row and file,
  capturing whatever risk/AI state is current at that moment; nothing is
  silently cached or skipped ("do not invent caching semantics that hide
  intentional regeneration").
* **Changed risk calculation version / recalculated risk / changed AI
  content** — naturally reflected as different `risk_calculation_version`
  / `source_risk_calculated_at` / `ai_recommendations_included` values on
  the newly generated row; no special "did anything change" detection is
  needed.
* **Changed report template version** — likewise simply recorded on the
  new row via `report_template_version`.
* **Failed generation** — no row is created and no file is published; any
  previously valid report for the same scan is left completely untouched.
* **Concurrency** — a unique constraint on `(scan_id, generated_at)`
  protects against two reports for the same scan sharing an identical
  generation instant; this is a defensive database-level invariant, not
  the primary duplicate-prevention mechanism (there is intentionally no
  "duplicate" concept for reports beyond this).

---

# Report Storage

Reports are stored as files under the configured `REPORT_OUTPUT_DIRECTORY`,
separate from all assessment data. Only the following are persisted in the
database — never an absolute path, and never client input:

* Report Identifier (`id`)
* Server-generated file name (`file_name`, formatted as `report_<id>.pdf`)
* Format (`format`)
* Size in bytes (`file_size_bytes`)
* Generation Time (`generated_at`)

## Atomic Publication

Generation renders to a temporary file inside the same storage root (so the
final move is atomic on the same filesystem), validates the result (file
exists, non-empty, begins with the `%PDF-` signature), and only then
publishes it via `os.replace()` into its final, server-controlled path. If
rendering or validation fails, the temporary file is removed and nothing is
exposed. If report metadata persistence fails *after* the file was
published, the orphaned file is removed and the transaction is rolled back
— no unmanaged file and no partial database record ever coexist.

## Path Security

Report file names are always server-generated
(`report_<uuid>.pdf`) — never derived from client input. Every path
resolution additionally verifies (`Path.is_relative_to`) that the resolved
file remains inside the configured storage root before it is read, as
defense-in-depth. No API response ever includes an internal filesystem
path; downloads are served through `GET /reports/{report_id}/download`
using a safe, server-generated `Content-Disposition` filename
(`avap-report-<report_id>.pdf`).

Report files should be immutable after generation.

---

# REST APIs

Base endpoint:

```text
/api/v1/reports
```

---

## Generate Report

```text
POST /reports
```

Body: `{"scan_id": "<uuid>"}`. Generates a new immutable report for the
scan's current assessment state (201). 404 if the scan does not exist; 422
if no deterministic risk assessment is available yet for the scan.

---

## List Reports

```text
GET /reports
```

Returns a paginated list of report metadata (`skip`, `limit`, optional
`scan_id` filter). Returns available reports.

---

## Get Report

```text
GET /reports/{report_id}
```

Returns report metadata.

---

## Download Report

```text
GET /reports/{report_id}/download
```

Downloads the generated report via `FileResponse` with
`media_type="application/pdf"` and a safe, server-generated download
filename. 404 if the report metadata or its physical file is missing.

---

## Delete Report

```text
DELETE /reports/{report_id}
```

Deletes stored report metadata and associated file according to retention policy.

---

# Data Flow

```text
Assessment Data

↓

Report Model

↓

Template Engine

↓

Report Generator

↓

Stored Report

↓

Client Download
```

No calculations occur during report generation.

---

# Security Requirements

The Reporting Engine shall:

* Generate reports only from trusted internal data
* Validate report requests
* Sanitize file names
* Prevent path traversal
* Restrict output directories
* Protect report storage

Reports should never expose:

* Internal stack traces
* Environment variables
* Credentials
* Debug information

---

# Error Handling

Possible failures include:

* Missing assessment
* Missing AI recommendation
* Template failure
* PDF generation failure
* File system error
* Storage failure

Errors should be returned using standardized report exceptions.

---

# Logging

The Reporting Engine should log:

* Report generation started
* Report generated
* Export format
* Generation duration
* Storage completed
* Download requests
* Generation failures

Logs should include:

* Report ID
* Scan ID
* Format
* Processing Time

Sensitive assessment data must not be logged.

---

# Dependencies

Depends on:

* Risk Assessment Module
* AI Engine
* Repository Layer
* Configuration Module

Communicates with:

* Report Repository

Does not communicate with:

* Scanner Engine
* Parser Engine

---

# Performance Considerations

The Reporting Engine should:

* Reuse report templates
* Cache static assets
* Minimize memory usage
* Generate reports efficiently
* Support asynchronous generation in future versions

Performance improvements must not alter report content.

---

# Future Enhancements

The architecture supports:

* HTML reports
* DOCX reports
* CSV exports
* Interactive dashboards
* Report scheduling
* Email delivery
* Digital signatures
* Report encryption
* Custom templates
* Organization branding
* Multi-language reports

These enhancements should integrate without modifying the Report Model.

---

# Testing Requirements

Implemented in `backend/tests/reporting/`, `backend/tests/repositories/test_report_repository.py`,
`backend/tests/services/test_report_service.py`, `backend/tests/services/test_report_integration.py`,
and `backend/tests/api/test_reports_api.py` (81 tests total, plus 2 regression
tests added to the existing `test_risk_repository.py`).

## Unit Tests

* Report Data Builder (`test_generator.py`): valid assembly, deterministic
  risk sourcing from Module 06, affected service inclusion, current/missing/
  stale AI recommendation handling, missing risk data, no ORM leakage,
  deterministic assembly for identical state
* Template Engine / safe-text escaping (`test_templates.py`): `<font>`,
  `<img>`, `<a href>`, malformed markup, very long strings
* PDF Generator (`test_pdf.py`): valid signature, executive summary/asset/
  finding rendering, missing remediation handling, long name/description/
  service/remediation values, empty assets section, multi-page reports,
  markup-injection payloads
* Repository (`test_report_repository.py`): create, retrieve by ID/scan,
  latest-by-scan, logical uniqueness, no commits

---

## Integration Tests

* PDF generation through the full Module 05 → 06 → 07 → 08 pipeline, using
  a fake AI provider at the real Module 07 provider boundary
* Report storage, atomic publication, download service, orphan file cleanup

---

## Security Tests

* Path traversal / absolute path rejection (`test_reporting/test_security.py`)
* Reporting Engine source code contains no AI provider or manager references
* No internal filesystem path ever appears in an API response

---

## API Tests

* Generate report, retrieve reports, list (with scan filter), download,
  delete, invalid UUID, missing scan/report/physical file, sanitized
  failures

All APIs are directly testable using Postman.

---

# Definition of Done

The Reporting Engine module is complete only when:

* [x] Report Model implemented (`app/models/report.py`, migration `0006`)
* [x] Report Data Builder implemented (`app/reporting/generator.py`)
* [x] Template Engine implemented (`app/reporting/templates.py`)
* [x] PDF Generator implemented (`app/reporting/pdf.py`)
* [x] Report Repository implemented (`app/repositories/report_repository.py`)
* [x] REST APIs completed (`/api/v1/reports/*`)
* [x] Unit tests passing
* [x] Integration tests passing
* [x] Security tests passing
* [x] API tests completed
* [x] Documentation updated
<!-- 
JSON Export is intentionally deferred (see "Implemented Architecture and
Scope" above); it is not part of this increment's Definition of Done. -->

Only after meeting all criteria may development proceed to the Dashboard APIs module.

---

# Related Documentation

* `modules_docs/07_ai_engine.md`
* `architecture_docs/system_architecture.md`
* `architecture_docs/data_flow.md`
* `architecture_docs/database.md`
* `architecture_docs/security.md`
* `architecture_docs/development_standards.md`
* `backend/backend.md`
