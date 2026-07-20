AVAP — Automated Vulnerability Assessment Platform

Full-stack security assessment platform. Pipeline:
Target Validation → Nmap Scan → Parse → Asset/Vuln Inventory → Deterministic Risk Scoring → AI Remediation (advisory) → PDF Report → Audit Trail.

Built for security awareness and learning. Free/open-source stack only.

Stack


Backend (backend/): Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, Pydantic v2, ReportLab, pytest (SQLite in-memory).
Frontend (frontend/): Next.js App Router, TypeScript, TanStack Query, Zustand, shadcn/ui + Tailwind, React Hook Form + Zod, Vitest.
Scanners: Nmap (live). OpenVAS adapter is a deliberate stub — writes a canned XML fixture, makes no network call.
AI: OpenRouter is the only built adapter. Groq/Gemini/HuggingFace are contract-ready config stubs with no adapter code.


Commands

Backend dev: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 (from backend/, venv active)
Backend tests: pytest
Backend checks: ruff check . · mypy . · bandit -r app · pip-audit
Frontend dev: npm run dev
Frontend checks: npm run test (vitest) · npm run typecheck (tsc --noEmit) · npm run lint (eslint)
Migrations: alembic upgrade head (11 migrations, 0001→0011)


Quality bar to match: 592 backend tests + 163 frontend tests passing, 0 lint/type/security findings (last hardening pass, 2026-07-19).

Architecture — non-negotiable

Backend layering. Route → Service → Repository → DB. No exceptions.


Services own business logic and own transactions/commits.
Repositories own persistence and flush only — a repository must never commit.
Routes contain zero business logic.
No DB access bypasses a repository. No raw SQL in business logic.
Layers talk only to adjacent layers. Dependencies point inward.


Frontend layering. Component → Feature Hook → API Service → Axios Client → Backend.


Feature-folder organization: features/{targets,scans,assets,vulnerabilities,risk,ai,reports,audit,dashboard}.
TanStack Query for server state. Zustand for UI state only.
Forms: React Hook Form + Zod.
Reuse the existing response envelope, error normalization, and loading/empty/error states. Do not invent parallel patterns.


App independence. Backend and frontend communicate only over versioned REST at /api/v1. No shared DB, session, or filesystem.

Pure-logic packages stay pure.


app/risk_engine/ — deterministic, versioned (CALCULATION_VERSION = "1.0.0"), frozen formula: severity base + asset/service bonuses, max-aggregated up the scope chain (vuln → asset → scan → assessment). AI must never influence risk scoring.
app/ai/ — provider-neutral abstraction, advisory output only, never a source of truth. Swapping providers must touch only the provider implementation.
app/reporting/ — PDF via ReportLab. Independent of scanners; adding a format must not change business logic. Requires risk calculated first.
app/audit/ — actor/request context. audit_events is append-only; a Postgres trigger blocks UPDATE/DELETE. Don't fight it.


Adapters. Scanners are reached only through their adapters; business logic never invokes CLI tools. Raw scanner output is never consumed directly — it always passes through a parser, which validates, normalizes, handles malformed input, and emits typed models. Parsers hold no business rules.

Security rules

Treat every input as hostile. Never shell=True, never concatenate shell commands, never hardcode credentials or secrets. Parameterized queries only. All config from environment variables. Guard against command injection, SQLi, path traversal, SSRF, XSS, RCE, unsafe deserialization. Errors returned to clients are sanitized; diagnostic detail goes to structured logs, never sensitive values.

Off-limits / out of scope

Do not add, even if it seems natural:


Authentication, RBAC, multi-user, multi-tenancy
Docker / Docker Compose / CI-CD
Message queues, scheduling, distributed scanners
Configurable sort order
New libraries or state-management patterns without asking


These are deliberate deferrals documented in project.md, not gaps. Current architecture must not prevent them later, but must not implement them now.

Conventions


Explicit type hints everywhere. Small functions, small classes, clear names.
Structured logging with module, operation, and failure reason.
No placeholder implementations, TODOs, dead code, commented-out code, print() statements, or unused imports in committed work.
Production code is not accepted without tests.
Architectural changes require explicit owner approval. Do not redesign established architecture unprompted.


Reference docs


Run.md — current "how to run this" (most authoritative, root)
ai_contract.md — full engineering contract; this file is its working summary
backend_api_manifest.yaml + Backend_Walk.md — API spec/walkthrough (gitignored, local-only)
modules_docs/01–10 — per-module specs
project.md — scope and deferred phases


If backend_api_manifest.yaml and running code disagree, trust the code and flag the drift.