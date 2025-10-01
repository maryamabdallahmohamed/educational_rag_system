
from sqlalchemy import Column, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.models import Base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class LearningUnit(Base):

    __tablename__ = "learning_units"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cpa_session_id = Column(UUID(as_uuid=True), ForeignKey("content_processor_agent.id", ondelete="CASCADE"))
    
    # Core unit content
    title = Column(Text, nullable=False)
    subtopics = Column(JSONB, nullable=True)  
    detailed_explanation = Column(Text, nullable=True)
    key_points = Column(JSONB, nullable=True)  

    # Educational metadata
    difficulty_level = Column(Text, nullable=True) 
    learning_objectives = Column(JSONB, nullable=True)
    keywords = Column(JSONB, nullable=True)
    
    # Classification
    subject = Column(Text, nullable=True)
    grade_level = Column(Text, nullable=True)
    
    # Source tracking
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    source_chunks = Column(JSONB, nullable=True) 
    
    # Metadata
    adaptation_applied = Column(Text, nullable=True)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    cpa_session = relationship("ContentProcessorAgent", back_populates="learning_units")
    source_document = relationship("Document")