# Backend (minimal FastAPI)

This folder contains a minimal FastAPI app that exposes two endpoints:

- `GET /health` — returns a simple health check
- `GET /specs` — lists markdown files in the top-level `specs/` folder

Setup (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

Docker build/run:

```bash
docker build -t rag_spec_backend .
docker run -p 8000:8000 rag_spec_backend
```
