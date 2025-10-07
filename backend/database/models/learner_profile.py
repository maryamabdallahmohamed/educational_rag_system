from sqlalchemy import Column, Text, DateTime, func, Integer, Float
from sqlalchemy.orm import relationship
from backend.database.models import Base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class LearnerProfile(Base):

    __tablename__ = "learner_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic learner information
    grade_level = Column(Integer, nullable=False)
    learning_style = Column(Text, nullable=True)  # "visual", "auditory", "kinesthetic", "mixed"
    preferred_language = Column(Text, default="en")
    difficulty_preference = Column(Text, default="medium")  # "easy", "medium", "hard"
    
    # Performance metrics
    avg_response_time = Column(Float, default=0.0)
    accuracy_rate = Column(Float, default=0.0)
    completion_rate = Column(Float, default=0.0)
    total_sessions = Column(Integer, default=0)
    
    # Behavioral and learning data
    interaction_patterns = Column(JSONB, nullable=True)  # For storing behavioral data
    learning_struggles = Column(JSONB, nullable=True)  # For tracking difficulty areas
    mastered_topics = Column(JSONB, nullable=True)  # For tracking completed topics
    preferred_explanation_styles = Column(JSONB, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sessions = relationship("TutoringSession", back_populates="learner", cascade="all, delete-orphan")
