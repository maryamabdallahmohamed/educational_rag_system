"""dispatchers.py

Maps routed types (action_type / route) to concrete handler functions.
Used by FULL_ROUTER_CHAIN in chains.py.
"""

from typing import Dict, Any
from uuid import UUID

from backend.core.action_agent.handlers.actions.add_note import add_note
from backend.core.action_agent.handlers.actions.next_section import next_section_handler
from backend.core.action_agent.handlers.actions.open_doc import open_doc_handler
from backend.core.action_agent.handlers.actions.prev_section import previous_section_handler
from backend.utils.logger_config import get_logger
from backend.utils.conversation_utils import save_conversation

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
    user_message = payload.get("user_message", "")
    session_id = payload.get("session_id")
    
    # Convert session_id to UUID if it's a string
    if session_id and isinstance(session_id, str):
        try:
            session_id_uuid = UUID(session_id)
        except (ValueError, AttributeError):
            logger.warning(f"Invalid session_id format: {session_id}")
            session_id_uuid = None
    else:
        session_id_uuid = session_id

    result = None
    
    if action_type == "open_doc":
        result = open_doc_handler(payload)
    elif action_type == "add_note":
        result = add_note(payload)
    elif action_type == "next_section":
        result = next_section_handler(payload)
    elif action_type == "prev_section":
        result = previous_section_handler(payload)
    else:
        result = {
            "status": "unknown_action",
            "action_type": action_type,
            "payload": payload,
        }
    
    # Save conversation to database asynchronously
    # Note: This is a sync function, so we need to handle async save differently
    # For now, we'll import asyncio and create a task
    if result and session_id_uuid:
        import asyncio
        ai_response_text = str(result) if not isinstance(result, str) else result
        try:
            # Try to get or create event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is running, create a task
                asyncio.create_task(save_conversation(
                    user_query=user_message,
                    ai_response=ai_response_text,
                    session_id=session_id_uuid
                ))
            else:
                # If no loop is running, run sync
                loop.run_until_complete(save_conversation(
                    user_query=user_message,
                    ai_response=ai_response_text,
                    session_id=session_id_uuid
                ))
        except Exception as e:
            logger.error(f"Failed to save action conversation: {str(e)}")
    
    return result


async def dispatch_query(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Async version - Called when intent_type == 'query'.

    Expected payload keys:
      - user_message: str
      - route: str  # "qa" | "summarization" | "agents"
      - route_confidence: float
      - route_details: str
      - session_id: str | None
    """
    route = payload.get("route")
    user_message = payload.get("user_message", "")
    session_id = payload.get("session_id")
    
    # Convert session_id to UUID if it's a string
    if session_id and isinstance(session_id, str):
        try:
            session_id = UUID(session_id)
        except (ValueError, AttributeError):
            logger.warning(f"Invalid session_id format: {session_id}")
            session_id = None
    
    result = None
    
    if route == "qa":
        if _qa_node is None:
            return {"error": "QA node not initialized. Call init_dispatchers first."}
        if "latest" not in _uploaded_documents:
            return {"error": "No document uploaded yet."}
        document = _uploaded_documents["latest"]
        result = await _qa_node.process(query=user_message, documents=[document], session_id=session_id)
        response = {"route": "qa", "result": result}
    
    elif route == "summarization":
        if _summarization_node is None:
            return {"error": "Summarization node not initialized. Call init_dispatchers first."}
        if "latest" not in _uploaded_documents:
            return {"error": "No document uploaded yet."}
        document = _uploaded_documents["latest"]
        result = await _summarization_node.process(query=user_message, documents=[document], session_id=session_id)
        response = {"route": "summarization", "result": result}
    
    elif route == "agents":
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
        result = tutor_result
        response = {"route": "agents", "result": tutor_result}
    
    else:
        response = {
            "status": "unknown_route",
            "route": route,
            "payload": payload,
        }
    
    # Save conversation to database
    if result and session_id:
        ai_response_text = str(result) if not isinstance(result, str) else result
        await save_conversation(
            user_query=user_message,
            ai_response=ai_response_text,
            session_id=session_id
        )
    
    return response
