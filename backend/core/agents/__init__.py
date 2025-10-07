"""
Agents module for content processing and tutoring
Simplified architecture with handler-based tools
"""

from .base_handler import BaseHandler
from .content_processor_agent import ContentProcessorAgent
from .tutor_agent import TutorAgent
from .cpa_handlers.explainable_units_handler import ExplainableUnitsHandler
from .cpa_handlers.rag_chat_handler import RAGChatHandler

__all__ = [
    'BaseHandler',
    'ContentProcessorAgent',
    'TutorAgent', 
    'ExplainableUnitsHandler',
    'RAGChatHandler'
]