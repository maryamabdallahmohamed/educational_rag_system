from .base import BaseEmbedder
from backend.config import DEVICE, CACHE_DIR
from typing import List
import asyncio
import os
from sentence_transformers import SentenceTransformer

# Set environment variable to disable tqdm completely
os.environ['TQDM_DISABLE'] = '1'




class HFEmbedder(BaseEmbedder):
    def __init__(self, model_name='sentence-transformers/gtr-t5-base', device=DEVICE):
        self.model = SentenceTransformer(model_name, device=device, cache_folder=CACHE_DIR)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents (for storing in vector DB)."""
        # Wrap the blocking operation in asyncio.to_thread
        embeddings = await asyncio.to_thread(
            self.model.encode, 
            texts, 
            convert_to_numpy=True, 
            show_progress_bar=False,
            normalize_embeddings=True
        )
        return embeddings.tolist()

    async def embed_query(self, text: str) -> List[float]:
        """Embed a single query (for similarity search)."""
        # Wrap the blocking operation in asyncio.to_thread
        embedding = await asyncio.to_thread(
            self.model.encode, 
            [text], 
            convert_to_numpy=True, 
            show_progress_bar=False,
            normalize_embeddings=True
        )
        return embedding[0].tolist()

    def _encode_sync(self, texts, **kwargs):
        """Helper method for synchronous encoding (used by asyncio.to_thread)"""
        return self.model.encode(texts, **kwargs)
    
