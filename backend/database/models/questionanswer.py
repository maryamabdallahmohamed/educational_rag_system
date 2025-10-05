from sqlalchemy import Column, Text, DateTime, Integer, String, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.database.models import Base
import uuid


class QuestionAnswer(Base):
    """Stores question-answer pairs in JSONB format."""
    
    __tablename__ = "question_answers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    qa_data = Column(JSONB, nullable=False)  
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    
    # Relationship to individual Q&A items
    qa_items = relationship("QuestionAnswerItem", back_populates="question_answer", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<QuestionAnswer(id={self.id})>"
