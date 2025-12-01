from typing import Dict, Any

def open_doc_handler(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Example stub. Replace with real logic (DB lookup, state update, etc.).
    """
    user_message = payload.get("user_message", "")
    return {
        "status": "ok",
        "action": "open_doc",
        "message": f"Would open document based on: {user_message}",
    }