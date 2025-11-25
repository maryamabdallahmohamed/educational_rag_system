"""
Tutor Agent Database Models

This module provides SQLAlchemy models that work with the existing
database schema for tutor-related tables:
- learner_profiles
- tutoring_sessions  
- learner_interactions

And adds new tables:
- topic_progress (new)
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid as uuid_lib
import enum

from .base import Base


class DifficultyLevelDB(enum.Enum):
    """Database enum for difficulty levels."""
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LearningStyleDB(enum.Enum):
    """Database enum for learning styles."""
    VISUAL = "visual"
    AUDITORY = "auditory"
    READING_WRITING = "reading_writing"
    KINESTHETIC = "kinesthetic"


# ============================================================================ #
# Existing Tables (mapped to work with existing schema)
# ============================================================================ #

class LearnerProfileModel(Base):
    """
    Maps to the existing 'learner_profiles' table.
    
    Stores persistent information about learners including their
    preferences, statistics, and learning progress.
    """
    __tablename__ = "learner_profiles"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    grade_level = Column(Integer, nullable=False, default=8)
    learning_style = Column(Text, nullable=True)
    preferred_language = Column(Text, nullable=True, default="en")
    difficulty_preference = Column(Text, nullable=True, default="intermediate")
    
    # Performance metrics
    avg_response_time = Column(Float, nullable=True)
    accuracy_rate = Column(Float, nullable=True, default=0.0)
    completion_rate = Column(Float, nullable=True, default=0.0)
    total_sessions = Column(Integer, nullable=True, default=0)
    
    # JSON fields for flexible data
    interaction_patterns = Column(JSONB, nullable=True, default=dict)
    learning_struggles = Column(JSONB, nullable=True, default=list)
    mastered_topics = Column(JSONB, nullable=True, default=list)
    preferred_explanation_styles = Column(JSONB, nullable=True, default=list)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("TutoringSessionDBModel", back_populates="learner")
    
    def __repr__(self):
        return f"<LearnerProfile(id={self.id}, grade_level={self.grade_level})>"
    
    @property
    def student_id(self) -> str:
        """Alias for compatibility with TutorAgent."""
        return str(self.id)
    
    @property
    def current_level(self) -> str:
        """Map difficulty_preference to DifficultyLevel."""
        return self.difficulty_preference or "intermediate"


class TutoringSessionDBModel(Base):
    """
    Maps to the existing 'tutoring_sessions' table.
    
    Records individual tutoring sessions including conversation history
    and performance metrics.
    """
    __tablename__ = "tutoring_sessions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learner_profiles.id"), nullable=True)
    cpa_session_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Session details
    current_topic = Column(Text, nullable=True)
    current_learning_unit_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Session data (stored as JSONB)
    session_state = Column(JSONB, nullable=True, default=dict)
    interaction_history = Column(JSONB, nullable=True, default=list)
    performance_summary = Column(JSONB, nullable=True, default=dict)
    
    # Status
    is_active = Column(Boolean, nullable=True, default=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    learner = relationship("LearnerProfileModel", back_populates="sessions")
    interactions = relationship("LearnerInteractionModel", back_populates="session")
    
    def __repr__(self):
        return f"<TutoringSession(id={self.id}, topic={self.current_topic})>"
    
    @property
    def session_id(self) -> str:
        """String representation of session ID."""
        return str(self.id)
    
    def add_interaction(self, role: str, content: str, metadata: dict = None):
        """Add an interaction to the history."""
        interaction = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        if self.interaction_history is None:
            self.interaction_history = []
        self.interaction_history = self.interaction_history + [interaction]
    
    def end_session(self, summary: dict = None):
        """Mark the session as ended."""
        self.ended_at = datetime.utcnow()
        self.is_active = False
        if summary:
            self.performance_summary = summary


class LearnerInteractionModel(Base):
    """
    Maps to the existing 'learner_interactions' table.
    
    Stores individual Q&A interactions for detailed analysis.
    """
    __tablename__ = "learner_interactions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("tutoring_sessions.id"), nullable=True)
    learning_unit_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Interaction details
    interaction_type = Column(Text, nullable=False, default="chat")
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    
    # Feedback
    was_helpful = Column(Boolean, nullable=True)
    difficulty_rating = Column(Integer, nullable=True)
    
    # Performance
    response_time_seconds = Column(Float, nullable=True)
    adaptation_requested = Column(Boolean, nullable=True, default=False)
    
    # Additional data
    interaction_metadata = Column(JSONB, nullable=True, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    session = relationship("TutoringSessionDBModel", back_populates="interactions")
    
    def __repr__(self):
        return f"<LearnerInteraction(id={self.id}, type={self.interaction_type})>"


# ============================================================================ #
# New Tables
# ============================================================================ #

class TopicProgressModel(Base):
    """
    NEW TABLE: Topic Progress Model.
    
    Tracks detailed progress for individual topics including
    mastery levels, practice statistics, and concept tracking.
    """
    __tablename__ = "topic_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_lib.uuid4)
    learner_id = Column(UUID(as_uuid=True), ForeignKey("learner_profiles.id"), nullable=False)
    
    # Topic info
    topic_id = Column(String(255), nullable=False)
    topic_name = Column(String(500), nullable=False)
    subject_area = Column(String(255), nullable=True)
    
    # Progress metrics
    mastery_level = Column(Float, default=0.0)  # 0.0 to 1.0
    confidence_score = Column(Float, default=0.0)  # 0.0 to 1.0
    
    # Detailed tracking (stored as JSONB)
    concepts_covered = Column(JSONB, default=list)
    concepts_mastered = Column(JSONB, default=list)
    concepts_struggling = Column(JSONB, default=list)
    
    # Practice stats
    practice_attempts = Column(Integer, default=0)
    practice_correct = Column(Integer, default=0)
    time_spent_minutes = Column(Integer, default=0)
    
    # Timestamps
    first_accessed = Column(DateTime(timezone=True), default=datetime.utcnow)
    last_accessed = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TopicProgress(topic={self.topic_name}, mastery={self.mastery_level})>"
    
    @property
    def accuracy(self) -> float:
        """Calculate topic-specific accuracy."""
        if self.practice_attempts == 0:
            return 0.0
        return self.practice_correct / self.practice_attempts
    
    def update_practice(self, correct: bool, time_minutes: int = 0):
        """Update practice statistics."""
        self.practice_attempts += 1
        if correct:
            self.practice_correct += 1
        self.time_spent_minutes += time_minutes
        self.last_accessed = datetime.utcnow()
        self._recalculate_mastery()
    
    def _recalculate_mastery(self):
        """Recalculate mastery level based on performance."""
        if self.practice_attempts < 3:
            self.mastery_level = self.accuracy * 0.5
        else:
            base_mastery = self.accuracy
            consistency_bonus = min(0.1, self.practice_attempts * 0.01)
            self.mastery_level = min(1.0, base_mastery + consistency_bonus)