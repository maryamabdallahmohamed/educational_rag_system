from sqlalchemy import Column, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.models import Base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class ToolOutput(Base):

    __tablename__ = "tool_outputs"

    tool_output_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_name = Column(Text, nullable=True)
    input_state = Column(JSONB, nullable=True)  
    output = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tutor_result_id = Column(UUID(as_uuid=True), ForeignKey("tutor_results.result_id", ondelete="CASCADE"), nullable=True)
    
    result = relationship("TutorResults", back_populates="tool_outputs")
