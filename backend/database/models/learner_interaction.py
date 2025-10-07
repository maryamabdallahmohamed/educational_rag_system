from sqlalchemy import Column, Text, DateTime, func, ForeignKey, Boolean, Integer, Float
from sqlalchemy.orm import relationship
from backend.database.models import Base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class LearnerInteraction(Base):

    __tablename__ = "learner_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("tutoring_sessions.id", ondelete="CASCADE"))
    learning_unit_id = Column(UUID(as_uuid=True), ForeignKey("learning_units.id", ondelete="SET NULL"), nullable=True)
    
    # Interaction details
    interaction_type = Column(Text, nullable=False)  # "question", "explanation", "practice", "assessment", "hint", "feedback"
    query_text = Column(Text, nullable=False)  # What the learner asked/did
    response_text = Column(Text, nullable=False)  # What the tutor provided
    
    # Feedback and metrics
    was_helpful = Column(Boolean, nullable=True)  # Learner feedback
    difficulty_rating = Column(Integer, nullable=True)  # 1-5 scale
    response_time_seconds = Column(Float, nullable=True)
    adaptation_requested = Column(Boolean, default=False)
    
    # Additional context
    interaction_metadata = Column(JSONB, nullable=True)  # For additional context
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("TutoringSession", back_populates="interactions")
    learning_unit = relationship("LearningUnit")
