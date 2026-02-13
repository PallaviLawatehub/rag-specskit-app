import os
import uuid
import tempfile
from pathlib import Path
import traceback
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from embedder import GeminiEmbedder
from document_processor import extract_text, chunk_text
from chroma_client import ChromaClient

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()

PORT = int(os.getenv("PORT", 5001))
COLLECTION_NAME = "rag_documents"  # ✅ Updated collection name

# ----------------------------
# Flask Setup
# ----------------------------
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
CORS(app)

@app.route("/")
def index():
    return app.send_static_file("index.html")

# ----------------------------
# Initialize Clients
# ----------------------------
CLIENTS_OK = False
ERROR_MSG = "Not initialized"

try:
    print("[INFO] Initializing Gemini embedder...")
    embedder = GeminiEmbedder(api_key=os.getenv("GOOGLE_API_KEY"))
    print("[INFO] Gemini embedder initialized [OK]")

    print("[INFO] Initializing ChromaDB client...")
    chroma = ChromaClient(
        api_key=os.getenv("CHROMA_API_KEY"),
        tenant_id=os.getenv("CHROMA_TENANT"),
        database_name=os.getenv("CHROMA_DATABASE"),
    )
    print("[INFO] ChromaDB client initialized [OK]")

    chroma.get_or_create_collection(COLLECTION_NAME)
    print(f"[INFO] Collection '{COLLECTION_NAME}' ready [OK]")

    CLIENTS_OK = True
    print("[INFO] All services initialized successfully [OK]")

except Exception as e:
    ERROR_MSG = str(e)
    print(f"[ERROR] Initialization failed: {ERROR_MSG}")

# ----------------------------
# Health Check
# ----------------------------
@app.route("/healthz", methods=["GET"])
def healthz():
    if not CLIENTS_OK:
        return jsonify({"status": "error", "details": ERROR_MSG}), 503

    chroma_health = chroma.health_check()
    return jsonify({
        "status": "ok",
        "gemini": True,
        "chroma": chroma_health["connected"],
        "database": os.getenv("CHROMA_DATABASE"),
        "collection": COLLECTION_NAME
    }), 200

# ----------------------------
# Upload Endpoint
# ----------------------------
@app.route("/api/upload", methods=["GET", "POST"])
def upload():
    # Allow a browser GET to show a helpful message instead of 404
    if request.method == "GET":
        return jsonify({"message": "Use POST to upload a file to this endpoint (multipart/form-data)."}), 200
    if not CLIENTS_OK:
        return jsonify({"error": ERROR_MSG}), 503

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    try:
        # Write uploaded file to a temporary path in a Windows-safe way
        # (NamedTemporaryFile can lock the file on Windows if left open).
        suffix = Path(file.filename).suffix or ""
        fd, temp_path = tempfile.mkstemp(suffix=suffix)
        try:
            with os.fdopen(fd, "wb") as out:
                # Read the uploaded file stream in chunks to avoid large memory use
                chunk = file.stream.read(8192)
                while chunk:
                    out.write(chunk)
                    chunk = file.stream.read(8192)
        except Exception:
            # Ensure temp file is removed on error
            try:
                os.unlink(temp_path)
            except Exception:
                pass
            raise

        text = extract_text(temp_path)
        print(f"[DEBUG] Extracted text length: {len(text) if text is not None else 'None'}")
        if not text or not text.strip():
            os.unlink(temp_path)
            return jsonify({"error": "No text extracted from file"}), 400

        chunks = chunk_text(text, chunk_size=500, overlap=50)
        print(f"[DEBUG] Produced {len(chunks)} chunks")
        if not chunks:
            os.unlink(temp_path)
            return jsonify({"error": "No chunks produced from file"}), 400

        embeddings = embedder.embed_texts(chunks)
        print(f"[DEBUG] Generated {len(embeddings)} embeddings")

        chunk_ids = [
            f"{file.filename}_{i}_{uuid.uuid4().hex[:8]}"
            for i in range(len(chunks))
        ]

        metadata = [
            {"source": file.filename, "chunk_index": i}
            for i in range(len(chunks))
        ]

        chroma.upsert_chunks(chunk_ids, chunks, embeddings, metadata)

        os.unlink(temp_path)

        return jsonify({
            "status": "success",
            "upload_id": uuid.uuid4().hex[:8],
            "chunks": len(chunks),
            "chunk_ids": chunk_ids,
            "collection": COLLECTION_NAME
        }), 200

    except Exception as e:
        print(f"[ERROR] Upload handler exception: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ----------------------------
# Answer Generation Helper
# ----------------------------
def generate_answer(query_text, chunks_data):
    """Use Gemini to synthesize an answer from relevant chunks."""
    if not chunks_data:
        return "No relevant documents found to answer your question."
    
    context = "\n".join([f"- {chunk['text']}" for chunk in chunks_data])
    
    try:
        import requests
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return _fallback_answer(query_text, chunks_data)
        
        # Try with gemini-2.0-flash (current model)
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        headers = {"Content-Type": "application/json"}
        
        prompt = f"""Based on the following documents, answer the user's question clearly and concisely.

Documents:
{context}

User Question: {query_text}

Please provide a direct, helpful answer."""
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        resp = requests.post(f"{url}?key={api_key}", json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        
        data = resp.json()
        if "candidates" in data and data["candidates"]:
            answer_text = data["candidates"][0]["content"]["parts"][0]["text"]
            return answer_text
        
        return _fallback_answer(query_text, chunks_data)
    
    except Exception as e:
        print(f"[WARNING] Gemini API failed: {e}, using fallback answer")
        return _fallback_answer(query_text, chunks_data)


def _fallback_answer(query_text, chunks_data):
    """Generate a simple fallback answer by extracting relevant text."""
    if not chunks_data:
        return "No relevant documents found."
    
    # Build answer from top chunks
    top_chunks = chunks_data[:3]
    answer_parts = []
    
    for chunk in top_chunks:
        text = chunk.get("text", "").strip()
        if text:
            answer_parts.append(text[:150] + ("..." if len(text) > 150 else ""))
    
    if answer_parts:
        return "Based on the documents:\n\n" + "\n\n".join(answer_parts)
    else:
        return "Unable to generate answer from the provided documents."


# ----------------------------
# Query Endpoint
# ----------------------------
@app.route("/api/query", methods=["POST"])
def query():
    if not CLIENTS_OK:
        return jsonify({"error": ERROR_MSG}), 503

    data = request.get_json() or {}
    query_text = data.get("query")
    top_k = int(data.get("top_k", 5))

    if not query_text:
        return jsonify({"error": "Query is required"}), 400

    try:
        # Generate embedding for user query
        query_embedding = embedder.embed_single(query_text)

        # Query Chroma collection
        results = chroma.query_similar(query_embedding, top_k=top_k)

        # Extract result components
        ids = results.get("ids", [])
        docs = results.get("documents", [])
        dists = results.get("distances", [])
        metas = results.get("metadatas", [])

        # Format results for frontend
        formatted_results = []
        for i in range(len(ids)):
            distance = dists[i] if i < len(dists) else None
            similarity_score = (1 - distance) if distance is not None else None

            formatted_results.append({
                "rank": i + 1,
                "text": docs[i] if i < len(docs) else "",
                "chunk_id": ids[i],
                "metadata": metas[i] if i < len(metas) else {},
                "similarity_score": round(similarity_score, 4) if similarity_score is not None else None
            })

        return jsonify({"results": formatted_results}), 200

    except Exception as e:
        print(f"[ERROR] Query exception: {e}")
        return jsonify({"error": str(e)}), 500


# ----------------------------
# Answer Endpoint (Query + LLM synthesis)
# ----------------------------
@app.route("/api/answer", methods=["POST"])
def answer():
    if not CLIENTS_OK:
        return jsonify({"error": ERROR_MSG}), 503

    data = request.get_json() or {}
    query_text = data.get("query")
    top_k = int(data.get("top_k", 5))

    if not query_text:
        return jsonify({"error": "Query is required"}), 400

    try:
        # Generate embedding for user query
        query_embedding = embedder.embed_single(query_text)

        # Query Chroma collection
        results = chroma.query_similar(query_embedding, top_k=top_k)

        # Extract result components
        ids = results.get("ids", [])
        docs = results.get("documents", [])
        dists = results.get("distances", [])
        metas = results.get("metadatas", [])

        # Format chunks for answer generation
        chunks = []
        for i in range(len(ids)):
            distance = dists[i] if i < len(dists) else None
            similarity_score = (1 - distance) if distance is not None else None

            chunks.append({
                "rank": i + 1,
                "text": docs[i] if i < len(docs) else "",
                "chunk_id": ids[i],
                "metadata": metas[i] if i < len(metas) else {},
                "similarity_score": round(similarity_score, 4) if similarity_score is not None else None
            })

        # Generate answer using synthesized response
        answer_text = generate_answer(query_text, chunks)

        return jsonify({
            "answer": answer_text,
            "sources": chunks,
            "source_count": len(chunks)
        }), 200

    except Exception as e:
        print(f"[ERROR] Answer exception: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ----------------------------
# Documents Endpoint (List all documents)
# ----------------------------
@app.route("/api/documents", methods=["GET"])
def get_documents():
    if not CLIENTS_OK:
        return jsonify({"error": ERROR_MSG}), 503

    try:
        limit = request.args.get("limit", 100, type=int)
        documents = chroma.get_all_documents(limit=limit)
        return jsonify({
            "status": "success",
            "documents": documents,
            "count": len(documents)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------------------------
# Collection Endpoint
# ----------------------------
@app.route("/api/collection", methods=["POST"])
def create_collection_endpoint():
    if not CLIENTS_OK:
        return jsonify({"error": ERROR_MSG}), 503

    try:
        data = request.get_json() or {}
        collection_name = data.get("name", COLLECTION_NAME)
        chroma.get_or_create_collection(collection_name)
        return jsonify({
            "status": "success",
            "collection": collection_name
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------------------------
# Reset Endpoint
# ----------------------------
@app.route("/api/reset", methods=["DELETE"])
def reset():
    if not CLIENTS_OK:
        return jsonify({"error": ERROR_MSG}), 503

    try:
        chroma.reset_collection(COLLECTION_NAME)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ----------------------------
# Stats Endpoint
# ----------------------------
@app.route("/api/stats", methods=["GET"])
def stats():
    if not CLIENTS_OK:
        return jsonify({"error": ERROR_MSG}), 503
    try:
        count = chroma.count_documents()
        return jsonify({"total_chunks": count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
