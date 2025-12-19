from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.db import NeonDatabase
from backend.database.repositories.conversation_repository import ConversationRepository
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/chat-history", tags=["chat-history"])

class ChatHistoryItem(BaseModel):
    id: str
    user_query: str
    ai_response: str
    created_at: datetime
    session_id: Optional[str] = None

    class Config:
        from_attributes = True

class ChatHistoryResponse(BaseModel):
    session_id: str
    total: int
    items: List[ChatHistoryItem]

@router.get("/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=500, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: AsyncSession = Depends(NeonDatabase.get_session)
):
    """
    Get chat history for a specific session.
    
    - **session_id**: The session UUID to retrieve chat history for
    - **limit**: Maximum number of items to return (1-500)
    - **offset**: Number of items to skip for pagination
    
    Returns all user queries and AI responses for the session, ordered by most recent first.
    """
    repo = ConversationRepository(db)
    
    # Fetch chat history for the session
    conversations = await repo.get_by_session_id(session_id, limit=limit, offset=offset)
    
    if not conversations:
        # Return empty list if no history found
        return ChatHistoryResponse(
            session_id=str(session_id),
            total=0,
            items=[]
        )
    
    # Convert to response format
    items = [
        ChatHistoryItem(
            id=str(convo.id),
            user_query=convo.user_query,
            ai_response=convo.ai_response,
            created_at=convo.created_at,
            session_id=str(convo.session_id) if convo.session_id else None
        )
        for convo in conversations
    ]
    
    return ChatHistoryResponse(
        session_id=str(session_id),
        total=len(items),
        items=items
    )
