from sqlalchemy import Column, Text, DateTime, Integer, String, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.database.models import Base
import uuid
class QuestionAnswerItem(Base):
    """References individual questions and answers from the JSONB."""
    
    __tablename__ = "question_answer_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_answer_id = Column(UUID(as_uuid=True), ForeignKey("question_answers.id", ondelete="CASCADE"), nullable=False)
    
    qa_index = Column(Integer, nullable=True) 
    
    question_text = Column(Text, nullable=True) 
    answer_text = Column(Text, nullable=True)  
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship back to parent
    question_answer = relationship("QuestionAnswer", back_populates="qa_items")
    