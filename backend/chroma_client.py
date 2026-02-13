from typing import List, Dict, Any
import chromadb


class ChromaClient:
    def __init__(self, api_key: str, tenant_id: str, database_name: str):
        try:
            self.client = chromadb.CloudClient(
                api_key=api_key,
                tenant=tenant_id,
                database=database_name,
            )
            self.collection = None
        except Exception as e:
            raise RuntimeError(f"ChromaDB connection error: {e}")

    def get_or_create_collection(self, collection_name: str):
        try:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            raise RuntimeError(f"Collection error: {e}")

    def upsert_chunks(
        self,
        chunk_ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadata: List[Dict],
    ):
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        self.collection.upsert(
            ids=chunk_ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadata,
        )

    def query_similar(self, embedding: List[float], top_k: int = 5):
        if not self.collection:
            raise RuntimeError("Collection not initialized")

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "distances", "metadatas"],
        )

        return {
            "ids": results["ids"][0],
            "documents": results["documents"][0],
            "distances": results["distances"][0],
            "metadatas": results["metadatas"][0],
        }

    def reset_collection(self, collection_name: str):
        if self.collection:
            self.client.delete_collection(name=collection_name)
        self.get_or_create_collection(collection_name)

    def health_check(self):
        try:
            self.client.heartbeat()
            return {"connected": True}
        except:
            return {"connected": False}

    def get_all_documents(self, limit: int = 100):
        """Retrieve all documents from the collection with pagination support."""
        if not self.collection:
            return []

        try:
            results = self.collection.get(limit=limit)
            documents = []
            for i in range(len(results.get("ids", []))):
                documents.append({
                    "id": results["ids"][i],
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i]
                })
            return documents
        except Exception as e:
            raise RuntimeError(f"ChromaDB get error: {e}")

    def count_documents(self):
        """Return total number of documents using paged GET requests.

        Chroma Cloud enforces a maximum `limit` per GET (e.g. 300). Requesting
        a very large limit causes a quota error. To avoid that, page through
        results using a safe batch size (defaults to 300) until fewer than
        `batch_size` items are returned.
        """
        if not self.collection:
            return 0

        batch_size = 300
        total = 0
        offset = 0

        try:
            while True:
                # collection.get supports limit and offset in the Cloud SDK
                results = self.collection.get(limit=batch_size, offset=offset)
                ids = results.get("ids", [])
                chunk_count = len(ids)
                total += chunk_count
                if chunk_count < batch_size:
                    break
                offset += chunk_count

            return total
        except Exception as e:
            # If paging fails for any reason, fall back to a safe single GET
            try:
                results = self.collection.get(limit=batch_size)
                return len(results.get("ids", []))
            except Exception as e2:
                raise RuntimeError(f"ChromaDB count error: {e} | fallback error: {e2}")
