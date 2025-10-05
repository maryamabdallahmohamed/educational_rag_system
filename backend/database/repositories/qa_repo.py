from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from uuid import UUID
from backend.database.models.questionanswer import QuestionAnswer
from typing import List, Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID


class QuestionAnswerRepository:
    """Repository for QuestionAnswer operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, qa_data: Dict[str, Any]):
        """Create a new question-answer record."""
        qa = QuestionAnswer(qa_data=qa_data)
        self.session.add(qa)
        await self.session.flush()  
        return qa
    
    async def get_by_id(self, qa_id: UUID):
        """Get a question-answer by ID."""
        result = await self.session.execute(
            select(QuestionAnswer).where(QuestionAnswer.id == qa_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, limit: int = 100, offset: int = 0):
        """Get all question-answers with pagination."""
        result = await self.session.execute(
            select(QuestionAnswer).limit(limit).offset(offset)
        )
        return result.scalars().all()
    
    async def update(self, qa_id: UUID, qa_data: Dict[str, Any]):
        """Update a question-answer record."""
        qa = await self.get_by_id(qa_id)
        if qa:
            qa.qa_data = qa_data
            await self.session.flush()  # Add await here
        return qa
    
    async def delete(self, qa_id: UUID) -> bool:
        """Delete a question-answer record."""
        qa = await self.get_by_id(qa_id)
        if qa:
            self.session.delete(qa)  # Remove await - delete() is sync
            await self.session.flush()  # Add await here
            return True
        return False