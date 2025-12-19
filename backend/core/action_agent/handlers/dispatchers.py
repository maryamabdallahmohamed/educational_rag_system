"""dispatchers.py

Maps routed types (action_type / route) to concrete handler functions.
Used by FULL_ROUTER_CHAIN in chains.py.
"""

from typing import Dict, Any

from backend.core.action_agent.handlers.actions.add_note import add_note
from backend.core.action_agent.handlers.actions.next_section import next_section_handler
from backend.core.action_agent.handlers.actions.open_doc import open_doc_handler
from backend.core.action_agent.handlers.actions.prev_section import previous_section_handler
from backend.utils.logger_config import get_logger

logger = get_logger("dispatcher")

# Singleton instances - will be set from main.py
_qa_node = None
_summarization_node = None
_cpa_agent = None
_tutor_agent = None
_uploaded_documents = None
_current_query = None


def init_dispatchers(qa_node, summarization_node, cpa_agent, tutor_agent, uploaded_documents, current_query):
    """Initialize dispatcher with shared instances from main.py"""
    global _qa_node, _summarization_node, _cpa_agent, _tutor_agent, _uploaded_documents, _current_query
    _qa_node = qa_node
    _summarization_node = summarization_node
    _cpa_agent = cpa_agent
    _tutor_agent = tutor_agent
    _uploaded_documents = uploaded_documents
    _current_query = current_query
    logger.info("Dispatchers initialized with shared instances")


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
        return add_note(payload)
    # if action_type == "open_chat":
    #     return open_chat_handler(payload)
    # if action_type == "close_chat":
    #     return close_chat_handler(payload)
    # if action_type == "bookmark":
    #     return bookmark_handler(payload)
    # if action_type == "show_bookmarks":
    #     return show_bookmarks_handler(payload)
    if action_type == "next_section":
        return next_section_handler(payload)
    if action_type == "prev_section":
        return previous_section_handler(payload)
    # if action_type == "location":
    #     return location_handler(payload)

    return {
        "status": "unknown_action",
        "action_type": action_type,
        "payload": payload,
    }


async def dispatch_query(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async version - Called when intent_type == 'query'.

    Expected payload keys:
      - user_message: str
      - route: str  # "qa" | "summarization" | "agents"
      - route_confidence: float
      - route_details: str
    """
    route = payload.get("route")
    user_message = payload.get("user_message", "")
    
    if route == "qa":
        if _qa_node is None:
            return {"error": "QA node not initialized. Call init_dispatchers first."}
        if "latest" not in _uploaded_documents:
            return {"error": "No document uploaded yet."}
        document = _uploaded_documents["latest"]
        result = await _qa_node.process(query=user_message, documents=[document], session_id=payload.get("session_id"))
        return {"route": "qa", "result": result}
    
    if route == "summarization":
        if _summarization_node is None:
            return {"error": "Summarization node not initialized. Call init_dispatchers first."}
        if "latest" not in _uploaded_documents:
            return {"error": "No document uploaded yet."}
        document = _uploaded_documents["latest"]
        result = await _summarization_node.process(query=user_message, documents=[document], session_id=payload.get("session_id"))
        return {"route": "summarization", "result": result}
    
    if route == "agents":
        if _cpa_agent is None or _tutor_agent is None:
            return {"error": "Agents not initialized. Call init_dispatchers first."}
        if "latest" not in _uploaded_documents:
            return {"error": "No document uploaded yet."}
        
        document = _uploaded_documents["latest"]
        previous_query = _current_query.get("latest", None)
        _current_query["latest"] = user_message
        
        cpa_result = await _cpa_agent.process(query=user_message, document=document)
        tutor_result = await _tutor_agent.process(
            query=user_message,
            cpa_result=cpa_result,
            current_query=_current_query,
            previous_query=previous_query
        )
        return {"route": "agents", "result": tutor_result}
    
    return {
        "status": "unknown_route",
        "route": route,
        "payload": payload,
    }
