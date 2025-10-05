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
    
    async def create(
        self,
        title: str,
        content: str,
        key_points: List[str],
        language: str = "ar"
    ) -> SummaryRecord:
        """Create a new summary record."""
        summary = SummaryRecord(
            title=title,
            content=content,
            key_points=key_points,
            language=language
        )
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
    
    async def get_by_language(self, language: str, limit: int = 100) -> List[SummaryRecord]:
        """Get summaries by language."""
        result = await self.session.execute(
            select(SummaryRecord)
            .where(SummaryRecord.language == language)
            .order_by(SummaryRecord.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def search_by_title(self, search_term: str, limit: int = 50) -> List[SummaryRecord]:
        """Search summaries by title (case-insensitive)."""
        result = await self.session.execute(
            select(SummaryRecord)
            .where(SummaryRecord.title.ilike(f"%{search_term}%"))
            .order_by(SummaryRecord.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def update(
        self,
        summary_id: UUID,
        title: Optional[str] = None,
        content: Optional[str] = None,
        key_points: Optional[List[str]] = None,
        language: Optional[str] = None
    ) -> Optional[SummaryRecord]:
        """Update a summary record."""
        summary = await self.get_by_id(summary_id)
        if summary:
            if title is not None:
                summary.title = title
            if content is not None:
                summary.content = content
            if key_points is not None:
                summary.key_points = key_points
            if language is not None:
                summary.language = language
            await self.session.flush()
        return summary
    
    async def delete(self, summary_id: UUID) -> bool:
        """Delete a summary record."""
        summary = await self.get_by_id(summary_id)
        if summary:
            self.session.delete(summary)
            await self.session.flush()
            return True
        return False