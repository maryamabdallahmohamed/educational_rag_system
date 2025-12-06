from sqlalchemy.future import select
from backend.database.models.document import Document
from .base_repo import BaseRepository
import uuid

class DocumentRepository(BaseRepository):
    async def add(self, title: str, content: dict, doc_metadata: dict = None, session_id: uuid.UUID = None):
        doc = Document(title=title, content=content, doc_metadata=doc_metadata, session_id=session_id)
        self.session.add(doc)
        await self.session.commit()
        await self.session.refresh(doc)
        return doc

    async def get(self, doc_id: int):
        result = await self.session.execute(select(Document).where(Document.id == doc_id))
        return result.scalar_one_or_none()
