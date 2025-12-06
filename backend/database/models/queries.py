# Queries

# query_id (PK)

# user_id (FK → Users)

# document_id (FK → Documents)

# query_text

# previous_query_id (FK → Queries, nullable)

# created_at
from sqlalchemy import Column, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.models import Base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

class Query(Base):
    __tablename__ = "queries"
    query_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"))
    query_text = Column(Text, nullable=False)
    previous_query_id = Column(UUID(as_uuid=True), ForeignKey("queries.query_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="queries")
    previous_query = relationship("Query", back_populates="next_queries", remote_side=[query_id])
    next_queries = relationship("Query", back_populates="previous_query")

