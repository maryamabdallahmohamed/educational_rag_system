"""
dispatchers.py

Maps routed types (action_type / route) to concrete handler functions.
Used by FULL_ROUTER_CHAIN in chains.py.
"""

from typing import Dict, Any

from backend.core.action_agent.handlers.actions.open_doc import open_doc_handler
from backend.core.action_agent.handlers.actions.next_section import next_section_handler





def dispatch_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Called when intent_type == 'action'.

    Expected payload keys:
      - user_message: str
      - session_id: str | None
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
        return {
            "action": "qa",
            "status": "success",
            "query": payload.get("user_message"),
            "details": "Route to QA Node"
        }
    if route == "summarization":
        return {
            "action": "summarization",
            "status": "success",
            "query": payload.get("user_message"),
            "details": "Route to Summarization Node"
        }

    # default: general chat / tutor
    return chat_handler(payload)