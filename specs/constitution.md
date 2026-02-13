Build POC-grade RAG knowledge system prioritizing:

- Cloud-first architecture (ChromaDB Cloud, no local vector storage)
- Zero local compute for embeddings (Gemini API handles all embedding operations)
- Minimal resource footprint (no model downloads, stateless backend)
- API key security (environment variables for ChromaDB and Gemini credentials)
- Fast cold starts (<2s from deploy to query-ready)
- Educational transparency (visible retrieval steps with similarity scores)
- Version compatibility: ChromaDB >=0.6.0 (v2 API required for cloud), numpy <2
- Port flexibility: Backend defaults to 5001
- Integration test coverage: Upload → query → reset cycle before declaring "done"
