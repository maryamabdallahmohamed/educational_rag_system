from typing import Dict, Any
from uuid import UUID

from backend.core.action_agent.handlers.actions.add_note import add_note
from backend.core.action_agent.handlers.actions.display_notes import display_note
from backend.core.action_agent.handlers.actions.next_section import next_section_handler
from backend.core.action_agent.handlers.actions.open_doc import open_doc_handler
from backend.core.action_agent.handlers.actions.prev_section import previous_section_handler
from backend.utils.logger_config import get_logger
from backend.database.repositories.conversation_repository import save_conversation
from backend.database.db import NeonDatabase
import os
from pdf2image import convert_from_path
from tqdm import tqdm   

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

def load_pdf(path: str, dpi: int = 300) -> list:
    """
    Converts a PDF or a folder of PDFs to a list of PIL Images.
    """
    images = []
    if os.path.isfile(path):
        if path.lower().endswith('.pdf'):
            images.extend(convert_from_path(path, dpi=dpi))
    elif os.path.isdir(path):
        for pdf_file in tqdm(os.listdir(path), desc="Converting PDFs"):
            if pdf_file.lower().endswith('.pdf'):
                pdf_path = os.path.join(path, pdf_file)
                images.extend(convert_from_path(pdf_path, dpi=dpi))   
    print(f"\n✅ PDF Conversion complete! Loaded {len(images)} pages.")
    return images


current_page = 0
async def dispatch_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Called when intent_type == 'action'.
    """
    global current_page  # Fix: Allow modification of global variable

    action_type = payload.get("action_type")
    user_message = payload.get("user_message", "")
    session_id = payload.get("session_id")
    
    # Resolve file path
    file_path = payload.get("file_path") or payload.get("file_paths")
    
    # If not in payload, fallback to latest uploaded document
    if not file_path and _uploaded_documents and "latest" in _uploaded_documents:
        doc = _uploaded_documents["latest"]
        if hasattr(doc, 'metadata') and doc.metadata and "source" in doc.metadata:
             file_path = doc.metadata["source"]

    # Normalize list to string if necessary
    if isinstance(file_path, list):
        if file_path:
            file_path = file_path[-1] # Take the most recent
        else:
            file_path = None
            
    pdf_pages = load_pdf(file_path) if file_path else None


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
        result = open_doc_handler(pdf_pages)
        if result.get("status") == "success":
            current_page = 0 # Reset to start
            
    elif action_type == "add_note":
        result = await add_note(payload)
        
    elif action_type == "next_section":
        result = await next_section_handler(pdf_pages, current_page)
        # Fix: Only increment if success
        if result.get("status") == "success":
            current_page = result.get("page_number", current_page + 1)
            
    elif action_type == "prev_section":
        result = await previous_section_handler(pdf_pages, current_page)
        # Fix: Only decrement if success
        if result.get("status") == "success":
            current_page = result.get("page_number", current_page - 1)
            
    elif action_type == "open_note":
        result = await display_note(payload)
    else:
        result = {
            "status": "unknown_action",
            "action_type": action_type,
            "payload": payload,
        }
    
    # Save conversation to database
    if result and session_id_uuid:
        ai_response_text = str(result) if not isinstance(result, str) else result
        try:
            await save_conversation(
                user_query=user_message,
                ai_response=ai_response_text,
                session_id=session_id_uuid
            )
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