"""
Agents module for content processing
Simplified architecture with handler-based tools
"""

from .base_handler import BaseHandler
from .content_processor_agent import ContentProcessorAgent
from .cpa_handlers.explainable_units_handler import ExplainableUnitsHandler
from .cpa_handlers.rag_chat_handler import RAGChatHandler
from .cpa_handlers.document_analysis_handler import DocumentAnalysisHandler

__all__ = [
    'BaseHandler',
    'ContentProcessorAgent', 
    'ExplainableUnitsHandler',
    'RAGChatHandler',
    'DocumentAnalysisHandler'
]