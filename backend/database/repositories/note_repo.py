from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.models.note import Note
from typing import Optional, Dict, Any, List
import uuid

class NoteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_note(self, note_text: str, session_id: Optional[uuid.UUID] = None, page_num: Optional[int] = None) -> Note:
        new_note = Note(
            note=note_text,
            page_num=str(page_num) if page_num is not None else None,
            session_id=session_id,
        )
        self.session.add(new_note)
        await self.session.commit()
        await self.session.refresh(new_note)
        return new_note


    async def get_notes_by_session(self, session_id: uuid.UUID) -> List[Note]:
        result = await self.session.execute(select(Note).where(Note.session_id == session_id))
        return result.scalars().all()
    async def get_notes_by_session_and_page(self, session_id: uuid.UUID, page_num: int) -> List[Note]:
        result = await self.session.execute(
            select(Note).where(
                Note.session_id == session_id,
                Note.page_num == str(page_num)
            )
        )
        return result.scalars().all()