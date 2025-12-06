# Tool Outputs (optional, for analytics/debugging)

# tool_output_id (PK)

# result_id (FK → TutorAgent Results)

# tool_name (e.g., "phrasing_info_tool" or "adaptive_tool")

# input_state (JSON)

# output (JSON or text)

# created_at
from sqlalchemy import Column, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.models import Base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class ToolOutput(Base):

    __tablename__ = "tool_outputs"

    tool_output_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id = Column(UUID(as_uuid=True), ForeignKey("queries.id", ondelete="CASCADE"))
    tool_name = Column(Text, nullable=True)
    input_state = Column(JSONB, nullable=True)  
    output = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    result = relationship("TutorResults", back_populates="tool_outputs")
