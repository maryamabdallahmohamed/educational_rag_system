from sqlalchemy import Column, String, JSON
from sqlalchemy.orm import relationship
from backend.database.models import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    content = Column(String, nullable=True)
    doc_metadata = Column(JSON, nullable=True)

    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
