# backend/database/repositories/chunk_repo.py
from sqlalchemy.future import select
from backend.database.models.chunks import Chunk
from .base_repo import BaseRepository
from sqlalchemy import text
import numpy as np

class ChunkRepository(BaseRepository):
    async def add(self, document_id: int, content: str, embedding: list,from_page : str):
        chunk = Chunk(document_id=document_id, content=content, embedding=embedding,from_page=from_page)
        self.session.add(chunk)
        await self.session.commit()
        await self.session.refresh(chunk)
        return chunk


    async def get_by_document(self, doc_id: int):
        result = await self.session.execute(select(Chunk).where(Chunk.document_id == doc_id))
        return result.scalars().all()
    async def get_by_page_number(self, page_number: int):
        result = await self.session.execute(select(Chunk).where(Chunk.from_page == page_number))
        return result.scalars().all()

    async def get_by_document_and_page(self, doc_id, page_number: str):
        result = await self.session.execute(
            select(Chunk).where(Chunk.document_id == doc_id, Chunk.from_page == page_number)
        )
        return result.scalars().all()
    
    async def get_similar_chunks(self, query_embedding: list, top_k: int = 5):
        """
        Retrieve top_k chunks by cosine similarity using pgvector's <=> (cosine distance).

        - Orders by embedding <=> query (cosine distance)
        - Returns both cosine_distance and cosine-based similarity_score (= 1 - distance)
        """

        # Normalize/validate input
        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.tolist()
        if not isinstance(query_embedding, (list, tuple)):
            raise ValueError("query_embedding must be a list, tuple, or numpy array")
        # Dimension check based on model definition Vector(768)
        if len(query_embedding) != 768:
            raise ValueError(f"query_embedding has dim {len(query_embedding)}, expected 768")

        # Convert to string format that pgvector expects: '[1.0,2.0,3.0]'
        embedding_str = str(query_embedding).replace(' ', '')

        # Use raw SQL with cosine distance operator <=> and cast parameter to vector
        result = await self.session.execute(
            text(
                """
                SELECT id, document_id, content, embedding,
                       (embedding <=> (:embedding_vector)::vector) AS cosine_distance
                FROM chunks
                ORDER BY embedding <=> (:embedding_vector)::vector
                LIMIT :limit_val
                """
            ),
            {
                "embedding_vector": embedding_str,
                "limit_val": top_k,
            },
        )

        # Convert results to Chunk objects with similarity scores
        chunks = []
        for row in result:
            chunk = Chunk()
            chunk.id = row.id
            chunk.document_id = row.document_id
            chunk.content = row.content
            chunk.embedding = row.embedding
            d = float(row.cosine_distance)
            chunk.cosine_distance = d
            chunk.similarity_distance = d
            chunk.similarity_score = 1.0 - d
            chunks.append(chunk)
        print("Similarity scores of retrieved chunks:")
        for chunk in chunks:
            print(f"Chunk ID: {chunk.id}, Similarity Score: {chunk.similarity_score}")

        return chunks
