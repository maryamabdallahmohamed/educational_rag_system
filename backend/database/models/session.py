from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.database.models import Base
import uuid

class Session(Base):
    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    metadata_ = Column("metadata", JSONB, nullable=True, default={})
