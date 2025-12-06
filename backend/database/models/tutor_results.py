from sqlalchemy import Column, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.models import Base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class TutorResults(Base):

    __tablename__ = "tutor_results"

    result_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id = Column(UUID(as_uuid=True), ForeignKey("queries.id", ondelete="CASCADE"))
    cpa_result = Column(JSONB, nullable=True)  
    tutor_result = Column(Text, nullable=True)
    current_state = Column(JSONB, nullable=True)  
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    query = relationship("Query", back_populates="tutor_results")
