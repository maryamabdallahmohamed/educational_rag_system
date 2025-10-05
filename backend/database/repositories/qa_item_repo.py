from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from uuid import UUID
from backend.database.models.qa_Item import QuestionAnswerItem
class QuestionAnswerItemRepository:
    """Repository for QuestionAnswerItem operations."""
    
    def __init__(self, db: Session):
        self.session = db
    
    async def create(
        self,
        question_answer_id: UUID,
        qa_index: Optional[int] = None,
        question_text: Optional[str] = None,
        answer_text: Optional[str] = None
    ):
        """Create a new question-answer item reference."""
        item = QuestionAnswerItem(
            question_answer_id=question_answer_id,
            qa_index=qa_index,
            question_text=question_text,
            answer_text=answer_text
        )
        self.session.add(item)
        await self.session.flush()  # Add await here
        return item
    
    async def get_by_id(self, item_id: UUID):
        """Get a question-answer item by ID."""
        result = await self.session.execute(
            select(QuestionAnswerItem).where(QuestionAnswerItem.id == item_id)
        )
        return result.scalar_one_or_none()
    

    
    async def delete(self, item_id: UUID) -> bool:
        """Delete a question-answer item."""
        item = await self.get_by_id(item_id)
        if item:
            self.session.delete(item)  # Remove await - delete() is sync
            await self.session.flush()  # Add await here
            return True
        return False