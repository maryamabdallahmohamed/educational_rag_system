from sqlalchemy import Column, Integer, Text, DateTime, Enum, func
import enum
from backend.database.models import Base

class RouteType(enum.Enum):
    QA = "qa"
    SUMMARIZATION = "summarization"
    CONTENT_PROCESSOR = "content_processor_agent"


class RouterDecision(Base):
    __tablename__ = "router_decisions"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(Text, nullable=False)
    chosen_route = Column(Enum(RouteType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())