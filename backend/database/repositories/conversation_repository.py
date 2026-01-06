from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.models import Conversation
from typing import List, Optional
from uuid import UUID

class ConversationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_query: str, ai_response: str, session_id: Optional[UUID] = None) -> Conversation:
        convo = Conversation(user_query=user_query, ai_response=ai_response, session_id=session_id)
        self.db.add(convo)
        await self.db.flush()
        return convo

    async def get_by_id(self, convo_id: UUID) -> Optional[Conversation]:
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == convo_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Conversation]:
        """List all conversations across sessions, ordered by most recent."""
        result = await self.db.execute(
            select(Conversation)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    async def get_by_session_id(self, session_id: UUID, limit: int = 100, offset: int = 0) -> List[Conversation]:
        """Get all conversations for a specific session, ordered by creation time."""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
