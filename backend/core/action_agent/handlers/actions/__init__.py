"""
handlers.actions

Action-level domain logic: open/close docs, notes, bookmarks, navigation, etc.
Each handler takes a `payload: Dict[str, Any]` and returns a dict response.
"""

from .open_doc import open_doc_handler
from .add_note import add_note_handler
from .open_chat import open_chat_handler
from .close_chat import close_chat_handler
from .bookmark import bookmark_handler
from .show_bookmarks import show_bookmarks_handler
from .next_section import next_section_handler
from .prev_section import prev_section_handler
from .location import location_handler

__all__ = [
    "open_doc_handler",
    "add_note_handler",
    "open_chat_handler",
    "close_chat_handler",
    "bookmark_handler",
    "show_bookmarks_handler",
    "next_section_handler",
    "prev_section_handler",
    "location_handler",
]