# Scanner Engine Module

**Module:** 03 - Scanner Engine

**File:** `modules_docs/03_scanner_engine.md`

**Version:** 1.0

**Status:** Implemented

---

# Purpose

The Scanner Engine is responsible for securely orchestrating the execution of supported security scanners, collecting their raw outputs as standardized scan artifacts, and delivering those artifacts to the Parser Engine without interpreting their contents.

The Scanner Engine acts as an execution framework rather than a scanner implementation. It provides a unified interface for integrating multiple security scanners while ensuring secure execution, process monitoring, timeout handling, and standardized output generation.

The Scanner Engine **does not**:

* Parse scanner output
* Store scan results
* Calculate risk
* Generate reports
* Perform AI analysis
* Access the database directly

Its sole responsibility is secure scanner execution.

---

# Module Responsibilities

The Scanner Engine is responsible for:

* Receiving scan execution requests
* Validating execution parameters
* Selecting the appropriate scanner adapter
* Executing supported scanners securely
* Monitoring scanner processes
* Handling execution timeouts
* Collecting scanner outputs
* Generating standardized Scan Artifacts
* Returning artifacts to the Parser Engine

The Scanner Engine must never interpret scanner-specific data.

---

# Design Principles

The Scanner Engine follows the following principles:

* Scanner Independence
* Adapter Pattern
* Factory Pattern
* Interface-based Design
* Secure Process Execution
* Single Responsibility Principle
* Extensibility
* Loose Coupling

Adding a new scanner should only require implementing a new adapter without modifying existing business logic.

---

# High-Level Architecture

```text
                Scan Management
                       │
                       ▼
               Scanner Manager
                       │
                       ▼
             Execution Validator
                       │
                       ▼
              Scanner Factory
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
     Nmap Adapter             OpenVAS Adapter
          │                         │
          └────────────┬────────────┘
                       ▼
               Scanner Executor
                       │
                       ▼
               Process Monitor
                       │
                       ▼
                Scan Artifact
                       │
                       ▼
                Parser Engine
```

---

# Internal Components

The Scanner Engine consists of the following components.

| Component           | Responsibility                                     |
| ------------------- | -------------------------------------------------- |
| Scanner Manager     | Entry point for all scanner execution requests     |
| Execution Validator | Validates scan execution requests before execution |
| Scanner Registry    | Maintains available scanner implementations        |
| Scanner Factory     | Resolves the appropriate scanner adapter           |
| Scanner Interface   | Standard contract for all scanner adapters         |
| Scanner Executor    | Securely executes scanner processes                |
| Process Monitor     | Tracks running scanner processes                   |
| Timeout Manager     | Terminates long-running scans safely               |
| Scan Artifact       | Standardized representation of scanner output      |
| Nmap Adapter        | Integrates Nmap                                    |
| OpenVAS Adapter     | Integrates OpenVAS Community Edition               |

---

# Scanner Execution Flow

```text
Scan Request

↓

Execution Validator

↓

Scanner Manager

↓

Scanner Factory

↓

Scanner Adapter

↓

Scanner Executor

↓

Process Monitor

↓

Scan Artifact

↓

Parser Engine
```

No component after the Scanner Engine receives direct process output.

---

# Scanner Interface

Every supported scanner must implement the same interface.

Responsibilities include:

* Preparing execution arguments
* Executing the scanner
* Collecting output
* Returning a Scan Artifact

The interface abstracts scanner-specific behavior from the rest of the application.

---

# Scanner Registry

The Scanner Registry maintains a catalog of supported scanners.

Current supported scanners:

* Nmap
* OpenVAS Community Edition

Future scanners may include:

* Masscan
* RustScan
* Nuclei
* Nikto
* Gobuster
* SSLyze
* Nessus
* Burp Enterprise
* Custom scanners

Adding new scanners should not require modifications to existing adapters or services.

---

# Scanner Factory

The Scanner Factory selects the appropriate adapter based on the requested scanner type.

```text
Scanner Type

↓

Factory

↓

Scanner Adapter
```

This prevents business logic from depending on concrete scanner implementations.

---

# Scanner Executor

The Scanner Executor is responsible for:

* Launching scanner processes
* Capturing stdout
* Capturing stderr
* Monitoring exit codes
* Enforcing execution limits
* Handling process termination

It does not interpret scanner output.

---

# Process Monitoring

During execution, the Process Monitor tracks:

* Process state
* Execution time
* Exit status
* Resource usage (future)
* Timeout events

Unexpected process failures are recorded and returned as execution errors.

---

# Timeout Management

Every scanner execution must enforce configurable timeout limits.

Responsibilities:

* Detect timeout conditions
* Terminate scanner processes safely
* Record timeout reason
* Return execution failure

Timeout duration is configurable through application settings.

---

# Scan Artifact

The Scanner Engine never returns raw XML, JSON, or text directly.

Instead, every execution produces a standardized Scan Artifact.

Typical fields include:

* Artifact ID
* Scanner Type
* Execution Status
* Exit Code
* Execution Time
* Output Location
* Standard Output
* Standard Error
* Metadata

The Parser Engine consumes Scan Artifacts rather than scanner-specific formats.

---

# Security Model

Scanner execution represents the highest-risk operation in the platform.

The Scanner Engine must enforce:

* Executable whitelist
* Argument validation
* Secure subprocess execution
* Execution timeout
* Resource limits (future)
* Exit code verification
* Output isolation
* Process cleanup

The following practices are prohibited:

* `shell=True`
* Dynamic command construction
* User-controlled executable paths
* Arbitrary command execution

---

# Scanner Isolation

The Scanner Engine communicates only with:

* Scan Management
* Scanner Adapters
* Parser Engine

It must never communicate directly with:

* Database
* Risk Engine
* AI Engine
* Reporting Engine

This separation preserves architectural boundaries.

---

# Data Flow

```text
Scan Request

↓

Scanner Execution

↓

Raw Scanner Output

↓

Scan Artifact

↓

Parser Engine
```

The Scanner Engine owns execution only.

Interpretation begins in the Parser Engine.

---

# Error Handling

Possible execution failures include:

* Scanner executable not found
* Invalid execution parameters
* Process timeout
* Scanner crash
* Permission denied
* Unsupported scanner
* Internal execution error

All failures are returned as structured execution results.

---

# Logging

The Scanner Engine should log:

* Scan started
* Scanner selected
* Scanner execution
* Process completion
* Exit code
* Timeout events
* Execution failures

Logs should include:

* Scan ID
* Scanner Type
* Execution Duration
* Exit Status

Sensitive information must never be logged.

---

# Dependencies

The Scanner Engine depends on:

* Scan Management Module
* Configuration Module
* Logging Module

It communicates with:

* Parser Engine

It does not depend on:

* Database
* Risk Engine
* AI Engine
* Reporting Engine

---

# REST API

The Scanner Engine does not expose REST APIs directly.

All scanner execution requests originate from the Scan Management module.

---

# Testing Requirements

## Unit Tests

* Scanner Factory
* Registry
* Adapter selection
* Execution Validator
* Timeout Manager
* Scan Artifact generation

---

## Integration Tests

* Nmap execution
* OpenVAS execution
* Process monitoring
* Timeout handling
* Failure scenarios

---

## Security Tests

* Command injection attempts
* Invalid executable paths
* Malformed scanner arguments
* Timeout enforcement
* Unauthorized scanner selection

---

# Future Enhancements

The architecture supports future capabilities including:

* Distributed scan workers
* Remote scanners
* SSH-based execution
* Containerized scanners
* Kubernetes execution
* Parallel scanner execution
* Queue-based execution
* Plugin discovery
* Dynamic scanner registration
* Resource scheduling

These enhancements should integrate without modifying the Scanner Engine's public contract.

---

# Definition of Done

The Scanner Engine module is complete only when:

* Scanner framework implemented
* Scanner Interface implemented
* Scanner Registry implemented
* Scanner Factory implemented
* Secure process execution implemented
* Timeout management implemented
* Scan Artifact implemented
* Nmap adapter integrated
* OpenVAS adapter integrated
* Unit tests passing
* Integration tests passing
* Security tests completed
* Documentation updated
* Git commit created according to project standards

Only after meeting all criteria may development proceed to the Parser Engine module.

---

# Related Documentation

* `modules_docs/02_scan_management.md`
* `architecture_docs/system_architecture.md`
* `architecture_docs/data_flow.md`
* `architecture_docs/security.md`
* `architecture_docs/development_standards.md`
* `backend/backend.md`
