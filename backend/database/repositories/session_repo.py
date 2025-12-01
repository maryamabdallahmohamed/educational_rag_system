from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from backend.database.models.session import Session
from typing import Optional, Dict, Any
import uuid

class SessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, metadata: Optional[Dict[str, Any]] = None) -> Session:
        new_session = Session(metadata_=metadata or {})
        self.session.add(new_session)
        await self.session.commit()
        await self.session.refresh(new_session)
        return new_session

    async def get_session(self, session_id: uuid.UUID) -> Optional[Session]:
        result = await self.session.execute(select(Session).where(Session.id == session_id))
        return result.scalars().first()

    async def update_session(self, session_id: uuid.UUID, metadata: Dict[str, Any]) -> Optional[Session]:
        stmt = (
            update(Session)
            .where(Session.id == session_id)
            .values(metadata_=metadata)
            .returning(Session)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalars().first()