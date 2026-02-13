# Implementation Plan - RAG Spec Kit

## Phase 1: Core Backend (DONE ✓)

### Backend Infrastructure

- Framework: Flask 3.0.0 with Flask-CORS
- Port: 5001 (avoids macOS port conflicts)
- Execution: Stateless Python process (no session affinity)
- Configuration: Load from `.env` via `python-dotenv`
- Health check: `/healthz` validates Gemini API + ChromaDB connectivity

**Deliverables**:

- ✅ `backend/app.py` - Main Flask application with all endpoints
- ✅ `backend/embedder.py` - GeminiEmbedder wrapper + fallback
- ✅ `backend/chroma_client.py` - ChromaDB Cloud wrapper
- ✅ `backend/document_processor.py` - Text extraction & chunking
- ✅ `backend/requirements.txt` - Dependency pinning
- ✅ `backend/README.md` - Curl examples for all endpoints

### Vector Store Setup

- Service: ChromaDB Cloud (no local SQLite fallback)
- Version: 0.6.0+ with v2 API
- Auth: API key + tenant ID from environment
- Collection: `rag_documents` (created on startup)
- Embeddings: 3072-dim vectors from Google Gemini

### Embedding Service

- Model: Google Gemini `text-embedding-004` (3072-dim)
- Request handling: Batch API calls with pagination (up to 100 texts/request)
- Fallback: Deterministic local embeddings (seeded numpy RNG) when API fails
- Latency target: <1s per 100 texts

### Document Processing Pipeline

- Input formats: `.txt`, `.pdf`, `.md`
- Text extraction:
  - PDF: PyPDF2 with UTF-8 fallback to latin-1
  - TXT/MD: Direct UTF-8 read with fallback
- Chunking: 500 character segments with 50 character overlap (no empty chunks)
- Storage: Each chunk maps to metadata `{source, chunk_index}`

## Phase 2: Frontend (DONE ✓)

### User Interface

- Serve: Flask static folder (single-page app at `/`)
- Framework: Vanilla JavaScript (no build, no npm)
- Styling: Plain CSS (no Tailwind, no preprocessor)
- Structure:
  - Upload widget (file input, progress bar)
  - Query widget (text input, results display)
  - Stats widget (chunk count, sync timestamp)
  - Reset button (confirmation modal)

### Client-Side Logic

- API base: `http://localhost:5001/api` (respects CORS)
- Data flows:
  - Upload: `FormData` → `/api/upload` → show chunks count
  - Query: JSON → `/api/answer` → display synthesized answer + sources
  - Stats: Poll `/api/stats` every 10s (background)
  - Reset: DELETE to `/api/reset` → clear results
- Error handling: Display errors in red text (not console only)
- Security: HTML escape all user-sourced strings (XSS prevention)

## Phase 3: API Contract (DONE ✓)

### Required Endpoints

| Endpoint          | Method | Input            | Output                            | Status |
| ----------------- | ------ | ---------------- | --------------------------------- | ------ |
| `/api/upload`     | POST   | multipart file   | `{status, chunks, chunk_ids}`     | ✅     |
| `/api/query`      | POST   | `{query, top_k}` | `{results: [...]}`                | ✅     |
| `/api/answer`     | POST   | `{query, top_k}` | `{answer, sources, source_count}` | ✅     |
| `/api/stats`      | GET    | —                | `{total_chunks}`                  | ✅     |
| `/api/documents`  | GET    | ?limit=100       | `{documents, count}`              | ✅     |
| `/api/collection` | POST   | `{name}`         | `{status, collection}`            | ✅     |
| `/api/reset`      | DELETE | —                | `{status}`                        | ✅     |
| `/healthz`        | GET    | —                | `{status, gemini, chroma, ...}`   | ✅     |

### Error Handling Contract

All errors return JSON `{"error": "message"}` with appropriate HTTP status:

- 400: Bad request (missing field, invalid query)
- 503: Service unavailable (API key invalid, ChromaDB down)
- 500: Server error (unexpected exception)

## Phase 4: Integration Tests (TO DO)

### Test Scenarios

1. **Happy Path**: Upload → Query → Raw results
2. **Answer Path**: Upload → Ask question → Get synthesized answer
3. **Stats Polling**: Upload → fetch stats → verify count increments
4. **Reset Cycle**: Upload → Reset → Verify count = 0
5. **Error Handling**: Send invalid JSON → Receive 400 error
6. **Empty Query**: Query with empty string → Receive 400 error

### Test Tools

- Framework: Python `unittest` or `pytest`
- Real credentials: Use actual ChromaDB Cloud + Gemini API (no mocks)
- Sample data: Small text/PDF files in `tests/fixtures/`
- Reporting: Terminal output + `test_results.xml`

**Files to Create**:

- `test_integration.py` - Full cycle tests
- `test_api_contract.py` - Endpoint validation
- `tests/fixtures/sample.txt` - Test document

### Before Release Checklist

- ✅ All integration tests passing
- ✅ Health check shows all services OK
- ✅ Upload → query → reset cycle works end-to-end
- ✅ No console errors in frontend
- ✅ No credentials in any committed file
- ✅ README includes deployment instructions

## Phase 5: Documentation (IN PROGRESS)

### Files to Create/Update

- ✅ `.specify/memory/constitution.md` - Project governance + principles
- ✅ `specs/specification.md` - Functional & non-functional requirements
- ✅ `specs/plan.md` - This file (implementation roadmap)
- ✅ `backend/README.md` - API documentation + curl examples
- ⏳ `.env.example` - Template with all required variables (no secrets)
- ⏳ `CONTRIBUTING.md` - Code review + testing guidelines
- ⏳ `DEPLOYMENT.md` - How to deploy to production

### Deployment Configuration

- Environment variables (required):
  - `GOOGLE_API_KEY` - Gemini API key
  - `CHROMA_API_KEY` - ChromaDB Cloud API key
  - `CHROMA_TENANT` - ChromaDB tenant ID
  - `CHROMA_DATABASE` - ChromaDB database name
- Environment variables (optional with defaults):
  - `PORT=5001`
  - `EMBEDDING_MODEL=text-embedding-004`
  - `ANSWER_MODEL=gemini-2.0-flash`
  - `CHUNK_SIZE=500`
  - `CHUNK_OVERLAP=50`

## Success Criteria

Phase complete when:

1. All endpoints return correct responses (verified via curl)
2. Integration tests pass end-to-end with real APIs
3. Frontend loads, uploads file, shows results without errors
4. Stats endpoint returns dynamic chunk count from database
5. No API keys or credentials in committed code
6. Code reviewed against Constitution (Principle III, IV, V)
7. README includes setup, run, and test instructions
