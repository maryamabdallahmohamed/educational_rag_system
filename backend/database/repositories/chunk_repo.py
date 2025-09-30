# backend/database/repositories/chunk_repo.py
from sqlalchemy.future import select
from backend.database.models.chunks import Chunk
from .base_repo import BaseRepository
from sqlalchemy import text
import numpy as np

class ChunkRepository(BaseRepository):
    async def add(self, document_id: int, content: str, embedding: list):
        chunk = Chunk(document_id=document_id, content=content, embedding=embedding)
        self.session.add(chunk)
        await self.session.commit()
        await self.session.refresh(chunk)
        return chunk

    async def get_by_document(self, doc_id: int):
        result = await self.session.execute(select(Chunk).where(Chunk.document_id == doc_id))
        return result.scalars().all()
    
    async def get_similar_chunks(self, query_embedding: list, top_k: int = 5):
        """
        Retrieve top_k chunks most similar to the query_embedding using cosine similarity.
        """

        # Convert embedding to proper format for pgvector
        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.tolist()

        # Convert to string format that pgvector expects: '[1.0, 2.0, 3.0]'
        embedding_str = str(query_embedding).replace(' ', '')

        # Use raw SQL with proper vector format and similarity scores
        result = await self.session.execute(
            text("""
                SELECT id, document_id, content, embedding,
                       (embedding <-> :embedding_vector) as similarity_distance
                FROM chunks
                ORDER BY embedding <-> :embedding_vector
                LIMIT :limit_val
            """),
            {
                "embedding_vector": embedding_str,
                "limit_val": top_k
            }
        )

        # Convert results to Chunk objects with similarity scores
        chunks = []
        for row in result:
            chunk = Chunk()
            chunk.id = row.id
            chunk.document_id = row.document_id
            chunk.content = row.content
            chunk.embedding = row.embedding
            # Add similarity score as an attribute (lower distance = higher similarity)
            chunk.similarity_distance = float(row.similarity_distance)
            chunk.similarity_score = 1.0 / (1.0 + chunk.similarity_distance)  # Convert to 0-1 score
            chunks.append(chunk)

        return chunks
