# backend/database/repositories/chunk_repo.py
from sqlalchemy.future import select
from backend.database.models.chunks import Chunk
from .base_repo import BaseRepository

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
