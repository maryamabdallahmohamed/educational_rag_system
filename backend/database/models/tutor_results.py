from sqlalchemy import Column, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.models import Base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class TutorResults(Base):

    __tablename__ = "tutor_results"

    result_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cpa_result = Column(JSONB, nullable=True)  
    tutor_result = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tool_outputs = relationship("ToolOutput", back_populates="result", cascade="all, delete-orphan")
