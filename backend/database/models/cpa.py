from sqlalchemy import Column,  Text
from backend.database.models import Base
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.dialects.postgresql import JSONB

class content_processor_agent(Base):
    __tablename__ = "content_procesor_agent"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query= Column(Text, nullable=False)
    response= Column(Text, nullable=True)
    Tool=Column(Text,nullable=False)
    chunks_used = Column(JSONB, nullable=True)
    similarity_scores = Column(JSONB, nullable=True)






