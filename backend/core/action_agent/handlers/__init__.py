"""
handlers package

Aggregates action and query handlers in one importable namespace.
"""

from .actions import (
    open_doc_handler,
    add_note_handler,
    open_chat_handler,
    close_chat_handler,
    bookmark_handler,
    show_bookmarks_handler,
    next_section_handler,
    prev_section_handler,
    location_handler,
)
from .queries import (
    qa_handler,
    summarization_handler,
    chat_handler,
)

__all__ = [
    # actions
    "open_doc_handler",
    "add_note_handler",
    "open_chat_handler",
    "close_chat_handler",
    "bookmark_handler",
    "show_bookmarks_handler",
    "next_section_handler",
    "prev_section_handler",
    "location_handler",
    # queries
    "qa_handler",
    "summarization_handler",
    "chat_handler",
]