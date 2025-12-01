"""
handlers.queries

Query-level domain logic for routed queries:
- qa_handler: testing / quizzing
- summarization_handler: summaries
- chat_handler: general explanation / discussion
"""

from .qa import qa_handler
from .summarization import summarization_handler
from .cpa import chat_handler

__all__ = [
    "qa_handler",
    "summarization_handler",
    "chat_handler",
]