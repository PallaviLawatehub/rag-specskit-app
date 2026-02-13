# Task Backlog - RAG Spec Kit

Organized by component and aligned with [Constitution](../../.specify/memory/constitution.md) principles.

## DONE ✅

### Setup & Dependencies

- ✅ Initialize git repository
- ✅ Create `.gitignore` (python, venv, .env, node_modules, .vscode)
- ✅ Set up Python 3.13 environment
- ✅ Pin dependencies in `requirements.txt` (chromadb>=0.6.0, numpy<2, Flask==3.0.0, requests, PyPDF2, python-dotenv, Flask-CORS)
- ✅ Install all dependencies with `pip install -r requirements.txt`
- ✅ Create `.env` with Google API key, ChromaDB credentials (local only, git-ignored)

### Backend: Gemini Embeddings

- ✅ Create `backend/embedder.py` with `GeminiEmbedder` class
- ✅ Implement `embed_texts()` for batch embedding (pagination ≤100 texts/request)
- ✅ Update model from deprecated `embedding-001` to `text-embedding-004` (3072-dim vectors)
- ✅ Add fallback embedding (deterministic numpy RNG when API fails)
- ✅ Validate embedding dimensions match ChromaDB collection

### Backend: Document Processing

- ✅ Create `backend/document_processor.py` with extraction + chunking
- ✅ Implement `extract_text()` supporting `.txt`, `.md`, `.pdf` (PyPDF2)
- ✅ Add UTF-8 encoding with latin-1 fallback for PDF extraction
- ✅ Filter out None/empty pages from PDF extraction
- ✅ Implement `chunk_text()` with configurable size (default 500) and overlap (default 50)
- ✅ Remove empty chunks from output

### Backend: ChromaDB Cloud Integration

- ✅ Create `backend/chroma_client.py` with `ChromaClient` class
- ✅ Implement cloud connection using API key + tenant ID + database name
- ✅ Implement `get_or_create_collection()` with cosine distance metric
- ✅ Implement `upsert_chunks()` for bulk insert/update
- ✅ Implement `query_similar()` for semantic search with top-K
- ✅ Implement `get_all_documents()` for listing chunks (pagination support)
- ✅ Implement `count_documents()` for dynamic stats (no hardcoded totals)
- ✅ Implement `reset_collection()` for clearing data

### Backend: Flask API - Core Endpoints

- ✅ Initialize Flask app with CORS support, static folder pointing to frontend
- ✅ Implement `/healthz` endpoint (validates Gemini + ChromaDB in status, no hardcoded OK)
- ✅ Implement `/api/upload` (POST multipart) → extract → chunk → embed → store
- ✅ Implement `/api/query` (POST JSON) → embed question → ranking → return results with scores
- ✅ Implement `/api/stats` (GET) → query ChromaDB for dynamic total_chunks count
- ✅ Implement `/api/reset` (DELETE) → clear collection entirely
- ✅ Fix Windows console encoding error (replace Unicode checkmarks with [OK])

### Backend: Flask API - Extended Endpoints

- ✅ Implement `/api/documents` (GET) → list all chunks with pagination (limit param)
- ✅ Implement `/api/collection` (POST) → create or switch collection
- ✅ Implement `/api/answer` (POST) → query + synthesize LLM answer
- ✅ Add `generate_answer()` helper function (uses Gemini `gemini-2.0-flash` model)
- ✅ Add fallback answer generation (concatenate chunk excerpts if API fails)

### Frontend: User Interface

- ✅ Create `frontend/index.html` with single-page app structure
- ✅ Implement file upload widget (form input, drag-drop, progress indicator)
- ✅ Implement query input widget (text field, "Ask" button)
- ✅ Implement results display (deduplicate by source, show chunk text + score)
- ✅ Implement stats widget (display total_chunks, last_sync timestamp)
- ✅ Implement reset button with confirmation dialog
- ✅ Add CSS styling (responsive layout, color scheme, hover states)

### Frontend: API Integration

- ✅ Set `API_BASE` to `http://localhost:5001/api`
- ✅ Implement `uploadFile()` function → POST multipart → show chunk count
- ✅ Implement `askQuery()` function → POST to `/api/answer` → display synthesized answer + sources
- ✅ Implement `fetchStats()` function → polling `/api/stats` every 10s (background)
- ✅ Implement `resetCollection()` function → DELETE `/api/reset`
- ✅ Add `escapeHtml()` for XSS prevention on all user-sourced output

### Code Quality

- ✅ Add docstrings to all Python functions (parameters, returns, raises)
- ✅ Remove Unicode printing issues from backend initialization
- ✅ Add error messages to console logs with [ERROR], [INFO], [WARNING] prefixes
- ✅ Validate configuration at startup (fail fast if missing env vars)
- ✅ Add `traceback.print_exc()` for debugging exception chains

## TO DO ⏳

### Documentation

- [ ] Create `.env.example` (template with all required variables, no actual secrets)
- [ ] Create `backend/README.md` with curl examples for all endpoints
- [ ] Create `CONTRIBUTING.md` with code review + testing guidelines
- [ ] Create `DEPLOYMENT.md` with production setup instructions
- [ ] Add inline comments to complex functions (answer generation, embedding fallback)

### Integration Testing (Constitution Principle V)

- [ ] Create `tests/fixtures/sample.txt` (100-word document)
- [ ] Create `tests/fixtures/sample.pdf` (multi-page test document)
- [ ] Create `test_integration.py` with pytest:
  - [ ] Test 1: Happy path — upload → query → verify results have similarity scores
  - [ ] Test 2: Answer path — upload → ask question → verify answer is non-empty
  - [ ] Test 3: Stats — upload → fetch stats → verify incremented
  - [ ] Test 4: Reset cycle — upload → reset → verify count=0 → upload new → verify count incremented
  - [ ] Test 5: Error handling — POST invalid JSON → receive 400
- [ ] Run integration tests with real credentials before release
- [ ] Document test results in test_results.xml

### Error Handling & Resilience

- [ ] Add timeout handling for Gemini API calls (currently 10s)
- [ ] Add retry logic for ChromaDB connection failures (exponential backoff)
- [ ] Handle file upload size limits (reject >50MB files with error message)
- [ ] Handle invalid UTF-8 sequences in document extraction (fallback to raw bytes)

### Performance & Optimization

- [ ] Profile embedding latency (target <1s for 100 texts)
- [ ] Cache embedding model config in memory (don't reload on every request)
- [ ] Batch multiple queries in `/api/documents` endpoint (pagination)
- [ ] Measure cold start time (target <2s until first request succeeds)

### Frontend Enhancements

- [ ] Add loading spinner during upload/query (show UI is thinking)
- [ ] Add copy-to-clipboard button for answer text
- [ ] Expand/collapse source chunks (collapse by default for readability)
- [ ] Show query execution time (time from request → response)
- [ ] Mobile-responsive stylesheet (test on 320px width)

### Security Hardening

- [ ] Add rate limiting middleware (e.g., 10 requests per 10 seconds per IP)
- [ ] Add file extension whitelist (only .txt, .md, .pdf; reject .exe, .zip, etc.)
- [ ] Log all API requests with timestamp + endpoint + user source (for audit trail)
- [ ] Rotate API keys periodically (document procedure)
- [ ] Add HTTPS-only flag for production deployments

### Deployment & Operations

- [ ] Create `Dockerfile` for containerized backend
- [ ] Create `docker-compose.yml` for local dev environment
- [ ] GitHub Actions workflow: lint (pylint) → test (pytest) → deploy
- [ ] Cloud deployment guide (Heroku, Vercel, or GCP Cloud Run)
- [ ] Monitoring dashboard (API response times, error rates, ChromaDB health)

### Advanced Features (Post-POC)

- [ ] Multi-user support with session management
- [ ] Document versioning (track edits, show version history)
- [ ] Advanced search filters (date range, source file, similarity threshold)
- [ ] Answer quality scoring (users rate "helpful" / "not helpful")
- [ ] Batch query API (upload CSV of questions, get answers for all)

## Definition of Done: Phase 1 (POC Release)

A task is DONE when:

1. ✅ Code committed with meaningful message (`feat: ...`, `fix: ...`)
2. ✅ Existing tests still pass (no regressions)
3. ✅ New code has docstrings or inline comments (non-obvious logic)
4. ✅ No hardcoded credentials or magic numbers
5. ✅ Follows Constitution Principles III (transparency), IV (security), V (testing)
6. ✅ Code review approved (at least one reviewer)
7. ✅ Works end-to-end on Windows with Python 3.13 + real APIs

Current Phase: **POC ✅** (all core features implemented)
Next Phase: **Hardening** (testing, documentation, deployment)
