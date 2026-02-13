# RAG Spec Kit - Functional Specification

## Overview

Build a Retrieval-Augmented Generation (RAG) knowledge system where users upload documents, ask natural-language questions, and receive synthesized answers backed by transparent source references.

**Architecture**: Cloud-first (ChromaDB Cloud + Google Gemini API), stateless Flask backend, vanilla JS frontend.

## Functional Requirements

### FR1: Document Upload & Processing

- Accept `.txt`, `.md`, `.pdf` files via multipart form-data (`/api/upload` endpoint)
- Extract text preserving document structure (UTF-8 with fallback to latin-1 for PDFs)
- Chunk into overlapping segments (default: 500 chars, 50 char overlap)
- Generate 3072-dim embeddings using Google Gemini `text-embedding-004`
- Store chunk text + embeddings + metadata in ChromaDB Cloud collection
- Return upload confirmation with chunk count and IDs

**Acceptance Criteria**:

- ✅ Upload 1KB txt file → receive 1-2 chunks within 3 seconds
- ✅ Upload 50KB PDF → 8-10 chunks extracted without errors
- ✅ Invalid file types rejected with 400 error
- ✅ No local copies of uploaded files retained

### FR2: Semantic Query & Retrieval

- Accept natural-language question via `/api/query` (POST JSON `{"query": "...", "top_k": 5}`)
- Embed question using same Gemini embedding model (consistent vector space)
- Query ChromaDB with cosine similarity search, return top-K chunks
- Include similarity scores (0-1 range) and chunk metadata in response
- **Explicitly show**: rank, text, source file, chunk index, similarity score

**Acceptance Criteria**:

- ✅ Query response within 2 seconds (including network latency)
- ✅ Similarity scores present and between 0-1
- ✅ Results ranked by descending similarity
- ✅ Empty query rejected with 400 error
- ✅ No results returns `[]` not error

### FR3: Answer Synthesis

- Accept question via `/api/answer` endpoint (POST JSON)
- Retrieve top-K relevant chunks (same as FR2)
- Pass question + top chunks to Google Gemini `gemini-2.0-flash` API
- Synthesize concise answer referencing document content
- Return structured response: `{answer, sources: [...], source_count}`
- **Fallback**: If Gemini API fails, return concatenated chunk excerpts

**Acceptance Criteria**:

- ✅ Answer endpoint returns within 10 seconds
- ✅ Answer is coherent natural language, not token soup
- ✅ Sources list included regardless of synthesis method
- ✅ Graceful fallback if API key invalid or quota exceeded

### FR4: Stats & Collection Management

- `/api/stats` (GET): Return `{"total_chunks": N}` dynamically from ChromaDB count
- `/api/documents` (GET): List all stored chunks with pagination (limit param)
- `/api/collection` (POST): Create or switch active collection
- `/api/reset` (DELETE): Remove all chunks from collection
- Count must reflect database truth, not local cache

**Acceptance Criteria**:

- ✅ Stats endpoint returns within 1 second
- ✅ Reset endpoint clears all data
- ✅ Chunk count updates immediately after upload/reset
- ✅ Pagination defaults limit=100, supports custom limit

### FR5: Service Health & Configuration

- `/healthz` endpoint returns `{status, gemini: bool, chroma: bool, database: string, collection: string}`
- Fail fast on startup if credentials missing or invalid
- Log initialization steps (Gemini: OK, ChromaDB: OK)
- No "stale" status; return 503 Service Unavailable if deps fail

**Acceptance Criteria**:

- ✅ Health check within 500ms
- ✅ Service refuses requests if CLIENTS_OK = false
- ✅ Environment variables validated at startup
- ✅ Clear error messages in logs if config fails

### FR6: Frontend User Interface

- Single-page app at `/` (served by Flask static folder)
- Upload widget: file input → drag-drop → progress bar → confirmation
- Search widget: text input → "Ask" button → results display
- Results: Show answer in green box, sources with snippet below
- Stats widget: Display total chunks, last sync time
- Reset button: Confirm dialog → DELETE reset
- Safe HTML render (escape user content)

**Acceptance Criteria**:

- ✅ Upload shows progress during file transfer
- ✅ Errors display in red text, not console only
- ✅ All inputs sanitized before display
- ✅ Stats auto-refresh every 10 seconds (visible update timestamp)
- ✅ No console errors after any user action

## Non-Functional Requirements

### NF1: Performance

- Cold start: <2 seconds from process start to query-ready
- First query: <10 seconds (including API latency)
- Stats endpoint: <1 second
- Single upload: <3 seconds for 1KB file
- All endpoints timeout if no response within 30 seconds

### NF2: Reliability

- No hardcoded API keys; all credentials from environment
- Graceful degradation: If Gemini API down, fallback to manual answer
- Retry-safe APIs: Duplicate uploads create new chunks (not errors)
- Connection pooling for ChromaDB (persistent session)

### NF3: Scalability

- Stateless backend: No local file caching, no sessions
- Horizontal scalable: Multiple backend instances share CloudDB
- No in-memory model loading (all compute on cloud)

### NF4: Security

- CORS enabled for cross-origin requests (safe defaults)
- No credential logging (mask API keys in debug output)
- HTML escape all user input before display
- File upload size limit: 50MB (configurable)
- Rate limiting: Not required for POC

### NF5: Observability

- All retrieval steps logged with timestamps
- Similarity scores visible to user (not hidden in black box)
- Chunk source and index shown (traceability)
- Errors include root cause, not generic "failed"

## API Response Examples

### POST /api/upload

**Request**:

```
multipart/form-data: file=document.pdf
```

**Response 200**:

```json
{
  "status": "success",
  "upload_id": "abc12345",
  "chunks": 5,
  "chunk_ids": ["document.pdf_0_xyz", "document.pdf_1_abc", ...],
  "collection": "rag_documents"
}
```

### POST /api/answer

**Request**:

```json
{
  "query": "What is RAG?",
  "top_k": 5
}
```

**Response 200**:

```json
{
  "answer": "RAG is a technique that combines retrieval of relevant documents with generative models to produce...",
  "sources": [
    {
      "rank": 1,
      "text": "Retrieval-Augmented Generation (RAG) combines...",
      "chunk_id": "doc_0_xyz",
      "metadata": { "source": "document.pdf", "chunk_index": 0 },
      "similarity_score": 0.92
    }
  ],
  "source_count": 3
}
```

### GET /api/stats

**Response 200**:

```json
{
  "total_chunks": 12
}
```

### GET /healthz

**Response 200**:

```json
{
  "status": "ok",
  "gemini": true,
  "chroma": true,
  "database": "rag_db",
  "collection": "rag_documents"
}
```

## Definition of Done

- ✅ All FR endpoints functional and tested
- ✅ All NF performance targets met (verified via load test)
- ✅ Integration test covers: upload → query → answer → reset → query empty
- ✅ Frontend loads and renders without console errors
- ✅ No credentials in any committed file (use .env.example + .gitignore)
- ✅ Code reviewed against [Constitution](../../.specify/memory/constitution.md)
- ✅ README includes curl examples for all endpoints
