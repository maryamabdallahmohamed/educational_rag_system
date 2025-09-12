import numpy as np
from sentence_transformers import SentenceTransformer, util
from .base import BaseEmbedder
from backend__.config import DEVICE, CACHE_DIR


from typing import List
from sentence_transformers import SentenceTransformer

class HFEmbedder(BaseEmbedder):
    def __init__(self, model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", device="cpu"):
        self.model = SentenceTransformer(model_name, device=device)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents (for storing in vector DB)."""
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query (for similarity search)."""
        embedding = self.model.encode([text], convert_to_numpy=True)
        return embedding[0].tolist()

