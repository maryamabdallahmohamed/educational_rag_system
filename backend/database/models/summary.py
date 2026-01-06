from sqlalchemy import Column, Text, DateTime, String, func, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from backend.database.models import Base
from sqlalchemy.orm import relationship
import uuid


class SummaryRecord(Base):
    """Stores document summaries."""
    
    __tablename__ = "summaries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    language = Column(String(10), nullable=False, default="ar")
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=True)
    

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    session_relation = relationship("Session", back_populates="summaries")
