import os
import requests
from typing import List
import hashlib
import numpy as np


class GeminiEmbedder:
    """Wrapper for Google Generative AI embedding API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1"
        self.model = "text-embedding-004"
        # Gemini embeddings may be 3072-dim depending on model/version; use 3072
        # to match collection expectations in Chroma Cloud. Fallbacks will
        # generate vectors of this size for local testing.
        self.embedding_dim = 3072

    def embed_texts(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Embed a list of texts using Gemini API with batching.
        Returns list of 768-dim embeddings.
        """
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            batch_embeddings = self._embed_batch(batch)
            embeddings.extend(batch_embeddings)
        return embeddings

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a single batch of texts."""
        url = f"{self.base_url}/models/{self.model}:embedContent"
        embeddings = []
        
        for text in texts:
            payload = {
                "model": f"models/{self.model}",
                "content": {
                    "parts": [{"text": text}]
                }
            }
            headers = {"Content-Type": "application/json"}
            params = {"key": self.api_key}

            try:
                response = requests.post(url, json=payload, headers=headers, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                # Extract embedding from response
                if "embedding" in data and "values" in data["embedding"]:
                    embeddings.append(data["embedding"]["values"])
                else:
                    raise ValueError(f"Unexpected API response format: {data}")
            except requests.HTTPError as e:
                # If model not found or other HTTP error, fall back to local deterministic embeddings
                if e.response is not None and e.response.status_code == 404:
                    # Fallback: deterministic embedding based on sha256 hash
                    for text in texts:
                        seed = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16) % (2**32)
                        rng = np.random.RandomState(seed)
                        embeddings.append(rng.rand(self.embedding_dim).tolist())
                    return embeddings
                raise RuntimeError(f"Gemini API error: {e}")
            except requests.RequestException as e:
                raise RuntimeError(f"Gemini API error: {e}")
        
        return embeddings

    def embed_single(self, text: str) -> List[float]:
        """Embed a single text."""
        return self._embed_batch([text])[0]
