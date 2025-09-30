from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.models.cpa import content_processor_agent   
from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

class content_processor_agent_repository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, query: str, response: str, Tool: str, chunks_used: list, scores: list) -> content_processor_agent:
        decision = content_processor_agent(
            query=query,
            response=response,
            Tool=Tool,
            chunks_used=chunks_used,
            similarity_scores=scores
        )
        self.db.add(decision)
        await self.db.commit()
        await self.db.refresh(decision)
        return decision



