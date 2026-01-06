from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from backend.database.models import Base
import uuid

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    metadata_ = Column("metadata", JSONB, nullable=True, default={})
    summaries = relationship("SummaryRecord", back_populates="session_relation")
    cpa_sessions = relationship("ContentProcessorAgent", back_populates="session_relation")
    questions = relationship("QuestionAnswer", back_populates="session_relation")
    question_answers = relationship("QuestionAnswer", back_populates="session_relation", overlaps="questions")
    tutor_results = relationship("TutorResults", back_populates="session_relation")
    notes = relationship("Note", back_populates="session_relation")
