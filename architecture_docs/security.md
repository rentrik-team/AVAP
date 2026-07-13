# Security Architecture

---

# Purpose

This document defines the security architecture of the Automated Vulnerability Assessment Platform (AVAP).

It establishes the security principles, trust boundaries, threat model, defensive controls, and architectural requirements that govern the design and implementation of the platform.

This document complements:

- `ai_contract.md`
- `development_standards.md`

It does not replace secure coding practices or implementation guidelines.

---

# Security Objectives

The platform is designed to satisfy the following security objectives:

- Protect scan infrastructure
- Protect collected vulnerability data
- Prevent unauthorized scanner execution
- Prevent misuse of scanning capabilities
- Protect sensitive configuration
- Maintain integrity of assessment results
- Ensure reliable auditability
- Minimize attack surface
- Support future enterprise security features

---

# Security Principles

The platform follows the following principles:

- Zero Trust
- Least Privilege
- Defense in Depth
- Secure by Default
- Fail Securely
- Explicit Trust Boundaries
- Principle of Complete Mediation
- Separation of Duties
- Minimize Attack Surface

Every architectural decision should reinforce these principles.

---

# Trust Boundaries

The platform contains multiple trust boundaries.

```
                  Untrusted

              Client Requests
                     │
─────────────────────┼─────────────────────

               REST API Layer

─────────────────────┼─────────────────────

             Business Services

─────────────────────┼─────────────────────

        Internal Processing Layer

─────────────────────┼─────────────────────

     Scanner Infrastructure

─────────────────────┼─────────────────────

     Operating System Resources

─────────────────────┼─────────────────────

             Trusted Resources
```

Data crossing a trust boundary must always be validated.

---

# Threat Model

The platform is designed assuming an attacker may attempt:

- Command Injection
- SQL Injection
- Path Traversal
- Server-Side Request Forgery (SSRF)
- Remote Code Execution
- XML Injection
- YAML Injection
- Malicious Scanner Input
- File Upload Attacks
- Resource Exhaustion
- Log Poisoning
- Configuration Disclosure
- Credential Theft
- API Abuse
- Privilege Escalation (Future)
- Denial of Service

The system architecture should actively mitigate these threats.

---

# Attack Surface

The exposed attack surface currently includes:

- REST APIs
- Scanner execution
- Configuration loading
- Database connections
- Report generation

Future attack surfaces:

- Authentication
- User management
- Dashboard
- Scheduled jobs
- WebSocket endpoints
- Plugin ecosystem

Each new component must undergo security review.

---

# Input Validation

Every external input is considered untrusted.

This includes:

- IP addresses
- CIDR ranges
- Hostnames
- URLs
- UUIDs
- File paths
- Query parameters
- Request bodies
- Scanner output
- Environment variables

Validation must occur before business processing.

---

# Scanner Security

Scanner execution represents the highest-risk component.

Security requirements:

- Never execute shell commands using `shell=True`
- Never concatenate shell commands
- Always invoke subprocesses using argument lists
- Validate every scanner argument
- Restrict executable locations
- Restrict scan scope
- Capture exit codes
- Capture execution failures
- Apply execution timeouts
- Log scanner execution

Future versions should execute scanners inside isolated containers or dedicated scan workers.

---

# Command Execution

All external command execution must satisfy:

- Explicit executable path
- Argument list only
- No shell expansion
- No user-controlled executable names
- No dynamic command construction

Correct:

```python
subprocess.run(
    ["/usr/bin/nmap", "-sV", target],
    check=True
)
```

Incorrect:

```python
subprocess.run(
    f"nmap -sV {target}",
    shell=True
)
```

---

# Network Security

The platform should only communicate with:

- Scanner services
- Database
- Configured AI providers
- Internal services

Outbound requests should never be arbitrary.

Future enhancements:

- Firewall rules
- Network segmentation
- Scanner isolation
- Egress filtering

---

# Database Security

The database should implement:

- Parameterized queries
- Least privilege database user
- Encrypted connections (production)
- Foreign keys
- Constraints
- Transactions
- Indexes

The application must never build SQL dynamically.

---

# Configuration Security

Sensitive configuration includes:

- Database credentials
- API keys
- AI provider keys
- Scanner credentials
- Encryption keys

Configuration must originate from:

```
.env
```

Production deployments should use dedicated secret management solutions.

Secrets must never appear in:

- Git
- Source code
- Logs
- Error messages

---

# Logging Security

Logs should contain:

- Timestamp
- Severity
- Module
- Operation
- Correlation ID — implemented (Module 10): a server-generated or
  validated-and-reused `X-Request-ID` (bounded length, restricted charset;
  malformed/oversized/control-character values are replaced with a fresh
  UUID4), propagated via `app.api.middleware.request_context` and echoed in
  the `X-Request-ID` response header

Logs must never contain:

- Passwords
- API keys
- Tokens
- Secrets
- Session identifiers
- Database credentials

Audit logs (Module 10, `AuditEvent`/`audit_events`) are immutable at two
distinct levels, and the distinction is deliberate:

- **Application-level (always):** no repository or API update/delete path
  exists for a persisted `AuditEvent`.
- **Database-level (PostgreSQL only):** migration `0007_audit_event` installs
  a trigger that rejects any `UPDATE`/`DELETE` on `audit_events`. This is
  genuine database-enforced append-only behavior, not merely an application
  convention — but it is not a cryptographic or tamper-evident guarantee
  (no hash chaining is implemented); see `modules_docs/10_audit_logging.md`
  for the exact guarantee boundary.

Audit metadata is server-generated only, recursively validated against a
forbidden-key/size/nesting policy (`app/audit/metadata_policy.py`) before
persistence, and never contains AI prompts, AI provider responses,
remediation content, report file paths, or raw exception text.

Client-supplied `X-Forwarded-For`/`X-Real-IP`/actor-identity headers are
never trusted for audit `source_ip`/actor attribution — only the direct
ASGI connection address is recorded, since no trusted reverse-proxy
configuration is documented for this deployment.

---

# File System Security

The platform should:

- Restrict writable directories
- Validate file paths
- Prevent path traversal
- Use absolute internal paths
- Restrict report output directories

User-controlled file paths are prohibited.

---

# Report Security

Generated reports may contain sensitive information.

Reports should:

- Be generated in controlled directories
- Prevent filename traversal
- Use sanitized filenames
- Restrict overwrite behavior

Future versions should support encrypted report storage.

---

# AI Security

AI responses must be treated as untrusted.

The AI engine:

- Cannot execute code
- Cannot modify risk scores
- Cannot bypass business rules
- Cannot access secrets
- Cannot directly interact with the database

AI is advisory only.

Risk calculations remain deterministic.

---

# API Security

Current APIs implement:

- Request validation
- Response validation
- Strong typing
- Consistent error handling

Future enhancements:

- Authentication
- Authorization
- RBAC
- API rate limiting
- API versioning
- API quotas

---

# Error Handling

Errors should:

- Never expose stack traces
- Never expose SQL
- Never expose internal paths
- Never expose secrets

Unexpected exceptions should be logged internally while returning sanitized client responses.

---

# Dependency Security

Dependencies should:

- Be actively maintained
- Come from trusted sources
- Be pinned to compatible versions
- Undergo periodic vulnerability review

Unused dependencies should be removed promptly.

---

# Data Protection

Sensitive information includes:

- Scan configurations
- Vulnerability results
- Internal asset inventory
- API credentials
- AI provider credentials

Future enhancements:

- Encryption at rest
- Encryption in transit
- Field-level encryption
- Secure backup strategy

---

# Security Monitoring

Future versions should support:

- Audit logging
- Security event monitoring
- Failed request monitoring
- Scan execution monitoring
- Configuration change auditing

---

# Security Testing

Every module should undergo:

- Unit testing
- Integration testing
- API testing

Future additions:

- Static Application Security Testing (SAST)
- Dependency scanning
- Dynamic Application Security Testing (DAST)
- Fuzz testing
- Container image scanning
- Penetration testing

---

# Incident Response Considerations

Future enterprise deployments should support:

- Centralized logging
- Audit trails
- Event correlation
- Security alerting
- Backup and recovery
- Forensic data preservation

---

# Future Security Enhancements

The architecture is intentionally designed to support:

- Authentication
- Multi-factor authentication
- RBAC
- Multi-tenancy
- Secrets Manager integration
- Distributed scan workers
- Container isolation
- TLS everywhere
- Certificate management
- Hardware Security Modules (HSM)
- Signed reports
- Secure plugin framework
- Compliance frameworks (CIS, ISO 27001, PCI DSS)

These features should integrate without requiring architectural redesign.

---

# Security Review Checklist

Every new feature should be reviewed for:

- Input validation
- Authorization impact
- Command execution
- File handling
- Database access
- Secret handling
- Logging
- Error handling
- Dependency usage
- Attack surface expansion

---

# Security Philosophy

Security is not a feature—it is a foundational architectural property.

Every component, module, API, integration, and future enhancement must be designed under the assumption that all external input is hostile and that failures should default to the safest possible behavior.


# Secret Management

The platform shall never store credentials inside source code.

All secrets shall originate from secure configuration sources.

Secrets include:

- Database credentials
- AI provider keys
- OpenVAS credentials
- JWT signing keys (future)
- Encryption keys
- API tokens
- OAuth secrets (future)

The repository shall only contain:

- .env.example

The following files must never be committed:

- .env
- .env.production
- .env.local
- secrets/*
- *.pem
- *.key
- *.crt

Production deployments should migrate to dedicated secret managers such as:

- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault

The application should fail during startup if required secrets are missing.