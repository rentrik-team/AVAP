# Risk Assessment Module

**Module:** 06 - Risk Assessment

**File:** `modules_docs/06_risk_assessment.md`

**Version:** 1.0

**Status:** Planned

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

Risk calculations are deterministic.

Current evaluation considers:

* Scanner severity
* CVSS score (if available)
* Number of affected assets
* Number of affected services

Future versions may additionally consider:

* Asset criticality
* Exploit availability
* Threat intelligence
* Business impact
* Exposure duration
* Environmental score

The architecture allows these enhancements without changing module boundaries.

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

The Risk Assessment entity typically contains:

* Risk Identifier
* Asset Identifier
* Vulnerability Identifier
* Risk Score
* Risk Level
* Calculation Version
* Calculation Timestamp
* Supporting Factors

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
* scan_jobs

The module owns only calculated risk records.

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

---

## Retrieve Risk by Asset

```text
GET /risk/assets/{asset_id}
```

---

## Retrieve Risk by Scan

```text
GET /risk/scans/{scan_id}
```

---

## Retrieve Overall Assessment

```text
GET /risk/summary
```

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

## Unit Tests

* Rule Engine
* Severity normalization
* Risk calculation
* Aggregation logic
* Context evaluation

---

## Integration Tests

* Assessment Package processing
* Repository persistence
* Asset aggregation
* Scan aggregation

---

## API Tests

* Risk retrieval
* Asset risk
* Scan risk
* Risk summary

All endpoints must be validated using Postman.

---

# Definition of Done

The Risk Assessment module is complete only when:

* Rule Engine implemented
* Severity Engine implemented
* Context Engine implemented
* Risk Calculation Engine implemented
* Risk Aggregation implemented
* Database persistence completed
* REST APIs completed
* Unit tests passing
* Integration tests passing
* API tests completed
* Documentation updated
* Git commit created according to project standards

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
