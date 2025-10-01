from sqlalchemy import Column,  Text
from backend.database.models import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.dialects.postgresql import JSONB

class ContentProcessorAgent(Base):
    __tablename__ = "content_processor_agent"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    tool_used = Column(Text, nullable=False)  
    # For RAG operations
    chunks_used = Column(JSONB, nullable=True)  
    similarity_scores = Column(JSONB, nullable=True)  
    units_generated_count = Column(Text, nullable=True)  
    
    
    # Relationship to learning units (if generated)
    learning_units = relationship("LearningUnit", back_populates="cpa_session", cascade="all, delete-orphan")


