from typing import Dict, Any

def open_doc_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example stub. Replace with real logic (DB lookup, state update, etc.).
    """
    doc_name = payload.get("action_details")
    session_id = payload.get("session_id")
    
    # Logic to find doc_id from doc_name (mocked or real)
    # ...
    
    return {
        "action": "open_doc",
        "status": "success",
        "details": f"Opening document: {doc_name}",
        "session_id": session_id
    }