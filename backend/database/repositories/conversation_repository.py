from sqlalchemy.orm import Session
from backend.database.models import Conversation
from typing import List, Optional

class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, user_query: str, ai_response: str) -> Conversation:
        convo = Conversation(user_query=user_query, ai_response=ai_response)
        self.db.add(convo)
        self.db.commit()
        self.db.refresh(convo)
        return convo

    def get_by_id(self, convo_id: int) -> Optional[Conversation]:
        return self.db.query(Conversation).filter(Conversation.id == convo_id).first()

    def list_all(self, limit: int = 100) -> List[Conversation]:
        return self.db.query(Conversation).order_by(Conversation.created_at.desc()).limit(limit).all()
