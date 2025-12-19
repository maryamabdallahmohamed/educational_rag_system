"""
Utility module for saving conversation history.
Used by action agent and other components to persist chat interactions.
"""
from typing import Optional
from uuid import UUID
from backend.database.db import NeonDatabase
from backend.database.repositories.conversation_repository import ConversationRepository
from backend.utils.logger_config import get_logger

logger = get_logger("conversation_utils")


async def save_conversation(
    user_query: str,
    ai_response: str,
    session_id: Optional[UUID] = None
) -> None:
    """
    Save a user query and AI response to the conversations table.
    
    Args:
        user_query: The user's question or message
        ai_response: The AI's response
        session_id: Optional session ID to associate the conversation with
    """
    try:
        async with NeonDatabase.get_session() as session:
            repo = ConversationRepository(session)
            conversation = await repo.create(
                user_query=user_query,
                ai_response=ai_response,
                session_id=session_id
            )
            await session.commit()
            logger.info(f"Saved conversation with ID: {conversation.id} for session: {session_id}")
    except Exception as e:
        logger.error(f"Failed to save conversation: {str(e)}")
        # Don't raise - conversation saving should not break the main flow
