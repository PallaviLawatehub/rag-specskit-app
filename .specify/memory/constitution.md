# RAG Spec Kit Constitution

Core governance and development principles for the Retrieval-Augmented Generation (RAG) knowledge system platform.

## Core Principles

### I. Cloud-First Architecture

**Non-negotiable requirement**: All persistent data and compute MUST run on cloud platforms. Local storage or computation is prohibited except for temporary build artifacts. ChromaDB Cloud handles vector storage; Google Gemini API handles embeddings. No local vector databases, no local LLM models, no downloaded weights.

**Rationale**: Minimizes resource footprint, enables fast cold starts (<2 seconds), ensures consistency across environments, simplifies deployment and scaling.

### II. API-First & Stateless Backend

Every feature MUST be exposed through HTTPS REST APIs. Backend server must be stateless—no local file caching, no in-memory model loading, no session affinity. All requests to ChromaDB, Gemini, or auxiliary services must be idempotent and retry-safe.

**Rationale**: Enables horizontal scaling, supports serverless deployment, simplifies testing and debugging, ensures reproducible behavior.

### III. Educational Transparency (Non-Negotiable)

All search results, embeddings, and confidence scores must be visible to users. Return similarity scores with ranked chunk matches. Log retrieval steps (query → embedding → ranking → answer) for inspection. Never hide intermediate steps or model decisions.

**Rationale**: Users understand system behavior, easier to debug retrieval failures, builds trust, supports learning.

### IV. API Key Security

All credentials (Google API Key, ChromaDB API Key, tenant ID, database name) MUST be stored in `.env` files or environment variables. NEVER commit credentials to git. Use `python-dotenv` for loading at runtime. Validate environment configuration at startup; fail fast if credentials missing.

**Rationale**: Prevents credential leakage, enables safe multi-environment deployment, simplifies credential rotation.

### V. Test-First Integration Coverage (Non-Negotiable)

Integration tests MUST cover the complete happy-path cycle: upload document → chunk & embed → query → retrieve answer → reset collection. Tests must use real credentials and real cloud services. New API endpoints require integration tests before merge.

**Rationale**: Ensures backend actually works end-to-end, catches API changes/deprecations before production, documents expected behavior.

## Technical Architecture Standards

### Backend Requirements

- **Framework**: Flask 3.0.0+ with Flask-CORS for cross-origin requests
- **Language**: Python 3.13+
- **Port**: Default 5001 (not 5000 due to macOS conflicts)
- **Vector Database**: ChromaDB Cloud v0.6.0+ (v2 API required), no fallback to local SQLite
- **Embeddings**: Google Gemini `text-embedding-004` (3072-dim vectors) with graceful fallback to deterministic local embeddings if API unavailable
- **LLM**: Google Gemini `gemini-2.0-flash` for answer synthesis
- **Document Formats**: PDF (via PyPDF2), plaintext, markdown with UTF-8 fallback encoding

### Frontend Requirements

- **Framework**: Vanilla JavaScript (no build step required)
- **Styling**: Plain CSS (no preprocessors)
- **APIs**: All requests to `http://localhost:5001/api/*` endpoints (respects frontend-backend separation)
- **Security**: HTML escape all user-sourced data before display (XSS prevention)

### Dependency Constraints

- `chromadb >=0.6.0` (required for cloud support)
- `numpy <2` (enforced by chromadb)
- `requests >=2.31.0` (for API calls)
- `python-dotenv >=1.0.0` (for config management)
- `Flask >=3.0.0`
- `PyPDF2 >=3.0.0` (for PDF extraction)

## API Contract & Endpoints

All endpoints return JSON with consistent error handling:

**Success Response**:

```json
{
  "status": "success",
  "data": {...}
}
```

**Error Response**:

```json
{
  "error": "Human-readable error message",
  "details": {...}
}
```

### Required Endpoints

| Method | Path              | Purpose                                                        | Auth      |
| ------ | ----------------- | -------------------------------------------------------------- | --------- |
| POST   | `/api/upload`     | Upload file (multipart) → extract text → chunk → embed → store | None      |
| POST   | `/api/query`      | Query → embed → rank chunks                                    | None      |
| POST   | `/api/answer`     | Query → embed → rank → synthesize answer via LLM               | None      |
| GET    | `/api/stats`      | Return total chunk count from database (dynamic)               | Read-only |
| GET    | `/api/documents`  | List all stored chunks with pagination                         | None      |
| POST   | `/api/collection` | Create or switch collection                                    | None      |
| DELETE | `/api/reset`      | Clear collection entirely                                      | None      |
| GET    | `/healthz`        | Service health check (Gemini + ChromaDB status)                | None      |

## Development Workflow

### Before Pushing Code

1. **Run integration tests**: `python -m pytest test_integration.py` (must pass with real credentials)
2. **Test upload cycle**: POST to `/api/upload` with sample `.pdf` or `.txt`
3. **Test query-answer cycle**: POST to `/api/answer` with natural language question
4. **Verify stats endpoint**: GET `/api/stats` returns `{"total_chunks": N}`
5. **Test reset**: DELETE `/api/reset` and verify collection is empty

### Documentation Requirements

- Every API endpoint documented in `backend/README.md` with curl examples
- Every Python function includes docstring with parameters, return type, raises
- Environment variables listed in `.env.example` (not `.env` itself)

### Code Review Gate (Non-Negotiable)

- All changes must include passing integration tests
- API changes must include frontend updates
- Deprecations must include migration guidance
- Breaking changes require 1-line explanation in commit message

## Deployment & Operations

### Configuration

All deployment-time values (API keys, ports, URLs, model names) must be configurable via environment:

```env
# Required
GOOGLE_API_KEY=...
CHROMA_API_KEY=...
CHROMA_TENANT=...
CHROMA_DATABASE=...

# Optional (with defaults)
PORT=5001
EMBEDDING_MODEL=text-embedding-004
ANSWER_MODEL=gemini-2.0-flash
CHUNK_SIZE=500
CHUNK_OVERLAP=50
```

### Cold Start Performance (SLA)

- Service ready to handle requests within 2 seconds of startup
- First query must complete within 10 seconds (including network latency)
- No pre-warming, no model downloading

## Versioning & Breaking Changes

**Version Format**: `MAJOR.MINOR.PATCH`

- **MAJOR**: Incompatible API changes (endpoint removed, response schema changed, new required env var)
- **MINOR**: New feature, new endpoint, added optional parameter
- **PATCH**: Bug fix, documentation, performance improvement, error message clarification

**Breaking Change Protocol**:

1. Add new endpoint alongside old one (both functional for ≥1 release)
2. Deprecation notice in documentation + `X-Deprecated` response header
3. Migrate tests and docs to new endpoint
4. Remove old endpoint in next MAJOR version

Current Version: `0.1.0` | Initial POC release with upload, query, answer synthesis.

## Governance

**Constitution Authority**: This document is the single source of truth for project principles. All other guidance (code review templates, CI/CD, deployment scripts) must align with these principles.

**Amendment Process**:

1. **Propose change**: Create issue describing principle change + rationale
2. **Design review**: Team consensus required (minimum 2 reviewers)
3. **Documentation**: Update constitution, create migration guide if breaking
4. **Validation**: Verify all existing code aligns with updated principle
5. **Version bump**: MINOR for additions, MAJOR for removals/redefinitions
6. **Commit message**: `docs: amend constitution to vX.Y.Z (add principle: ...)`

**Compliance Verification**:

- Pull request must reference passing integration tests
- Code review must verify against applicable principles
- CircleCI/GitHub Actions must enforce lint, type checks, test coverage

**Non-Negotiable Principles** (cannot be amended without complete project reset):

- III. Educational Transparency (users must see retrieval steps)
- IV. API Key Security (credentials never in code)
- V. Test-First Integration Coverage (real cloud services required)

**Version**: 0.1.0 | **Ratified**: 2026-02-13 | **Last Amended**: 2026-02-13
