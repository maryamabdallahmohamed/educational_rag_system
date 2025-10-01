from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from backend.database.models.cpa import ContentProcessorAgent
from typing import Optional, List
import uuid
from datetime import datetime


class ContentProcessorAgentRepository:
    """Repository for ContentProcessorAgent operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create( self,  query: str,  response: str, tool_used: str, chunks_used: Optional[list] = None, similarity_scores: Optional[list] = None,units_generated_count: Optional[str] = None
    ) -> ContentProcessorAgent:

        cpa_record = ContentProcessorAgent(
            query=query,
            response=response,
            tool_used=tool_used,
            chunks_used=chunks_used,
            similarity_scores=similarity_scores,
            units_generated_count=units_generated_count
        )
        self.session.add(cpa_record)
        await self.session.commit()
        await self.session.refresh(cpa_record)
        return cpa_record
