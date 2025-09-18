"""
Conversation Management Utilities
"""

from typing import List, Dict, Any
from datetime import datetime


class ConversationManager:
    """
    Manages conversation state and history
    """
    
    @staticmethod
    def format_conversation_history(messages: List[Dict[str, Any]]) -> str:
        """Format conversation history for prompt inclusion"""
        if not messages:
            return "No previous conversation."
        
        formatted = []
        for msg in messages[-6:]:  # Last 3 exchanges
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            
            if role == "user":
                formatted.append(f"User: {content}")
            elif role == "assistant":
                formatted.append(f"Assistant: {content}")
        
        return "\n".join(formatted)
    
    @staticmethod
    def add_message_to_history(
        history: List[Dict[str, Any]], 
        role: str, 
        content: str
    ) -> List[Dict[str, Any]]:
        """Add a message to conversation history"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        history.append(message)
        
        # Keep only last 20 messages to prevent memory bloat
        if len(history) > 20:
            history = history[-20:]
        
        return history
    
    @staticmethod
    def clear_history() -> List[Dict[str, Any]]:
        """Clear conversation history"""
        return []