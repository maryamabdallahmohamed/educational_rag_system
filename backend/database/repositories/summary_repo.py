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
    
    async def create(self, content: str) -> SummaryRecord:
        """Create a new summary record."""
        summary = SummaryRecord(content=content)
        self.session.add(summary)
        await self.session.flush()
        return summary
    
    async def get_by_id(self, summary_id: UUID) -> Optional[SummaryRecord]:
        """Get a summary by ID."""
        result = await self.session.execute(
            select(SummaryRecord).where(SummaryRecord.id == summary_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[SummaryRecord]:
        """Get all summaries with pagination."""
        result = await self.session.execute(
            select(SummaryRecord)
            .order_by(SummaryRecord.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
