# backend/database/repositories/summary_repo.py
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from backend.database.models.summary import SummaryRecord


class SummaryRepository:
    """Repository for Summary operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, content: str, language: str = "ar", session_id: UUID = None) -> SummaryRecord:
        """Create a new summary record."""
        summary = SummaryRecord(
            content=content,
            language=language,
            session_id=session_id
        )
        self.session.add(summary)
        await self.session.flush()
        return summary
    
    async def get_by_id(self, session_id: UUID) -> Optional[SummaryRecord]:
        """Get a summary by ID."""
        result = await self.session.execute(
            select(SummaryRecord).where(SummaryRecord.session_id == session_id)
        )
        return result.scalar_one_or_none()
    