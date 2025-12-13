from sqlalchemy import Column, Text, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from backend.database.models import Base
import uuid


class SummaryRecord(Base):
    """Stores document summaries."""
    
    __tablename__ = "summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)

    

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
