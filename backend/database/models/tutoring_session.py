from sqlalchemy import Column, Text, DateTime, func, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.database.models import Base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class TutoringSession(Base):

    __tablename__ = "tutoring_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learner_profiles.id", ondelete="CASCADE"))
    cpa_session_id = Column(UUID(as_uuid=True), ForeignKey("content_processor_agent.id", ondelete="SET NULL"), nullable=True)
    
    # Session content tracking
    current_topic = Column(Text, nullable=True)
    current_learning_unit_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to learning_units
    
    # Session data
    session_state = Column(JSONB, nullable=True)  # Topic progress, current exercise, etc.
    interaction_history = Column(JSONB, nullable=True)  # Conversation flow
    performance_summary = Column(JSONB, nullable=True)  # Session-level metrics
    
    # Session status
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    learner = relationship("LearnerProfile", back_populates="sessions")
    cpa_session = relationship("ContentProcessorAgent")
    interactions = relationship("LearnerInteraction", back_populates="session", cascade="all, delete-orphan")
