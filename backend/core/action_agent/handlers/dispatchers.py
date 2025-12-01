"""
dispatchers.py

Maps routed types (action_type / route) to concrete handler functions.
Used by FULL_ROUTER_CHAIN in chains.py.
"""

from typing import Dict, Any

from handlers import (
    # actions
    open_doc_handler,
    add_note_handler,
    open_chat_handler,
    close_chat_handler,
    bookmark_handler,
    show_bookmarks_handler,
    next_section_handler,
    prev_section_handler,
    location_handler,
    # queries
    qa_handler,
    summarization_handler,
    chat_handler,
)


def dispatch_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Called when intent_type == 'action'.

    Expected payload keys:
      - user_message: str
      - action_type: str
      - action_confidence: float
      - action_details: str
    """
    action_type = payload.get("action_type")

    if action_type == "open_doc":
        return open_doc_handler(payload)
    if action_type == "add_note":
        return add_note_handler(payload)
    if action_type == "open_chat":
        return open_chat_handler(payload)
    if action_type == "close_chat":
        return close_chat_handler(payload)
    if action_type == "bookmark":
        return bookmark_handler(payload)
    if action_type == "show_bookmarks":
        return show_bookmarks_handler(payload)
    if action_type == "next_section":
        return next_section_handler(payload)
    if action_type == "prev_section":
        return prev_section_handler(payload)
    if action_type == "location":
        return location_handler(payload)

    return {
        "status": "unknown_action",
        "action_type": action_type,
        "payload": payload,
    }


def dispatch_query(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Called when intent_type == 'query'.

    Expected payload keys:
      - user_message: str
      - route: str  # "qa" | "summarization" | "content_processor_agent"
      - route_confidence: float
      - route_details: str
    """
    route = payload.get("route")

    if route == "qa":
        return qa_handler(payload)
    if route == "summarization":
        return summarization_handler(payload)

    # default: general chat / tutor
    return chat_handler(payload)