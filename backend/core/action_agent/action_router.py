"""
action_router.py

Backend-ready action router using SUBACTION_ROUTER_PROMPT and GroqLLM.
Maps messages to concrete action types like "open_doc", "add_note", etc.
"""

import re
import json
from typing import Dict, Any

from backend.core.action_agent.prompts import SUBACTION_ROUTER_PROMPT
from backend.models.llms.ollama_llm import OllamaLLM  

# Shared LLM wrapper instance
_llm_wrapper = OllamaLLM()

JSON_BLOCK_REGEX = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json_block(text: str) -> Dict[str, Any]:
    """
    Extract the first JSON-like block from the LLM output and parse it.
    Returns {} if parsing fails.
    """
    match = JSON_BLOCK_REGEX.search(text)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


def route_action_message(user_message: str) -> Dict[str, Any]:
    """
    Route an action-style message to a concrete action type.

    Parameters
    ----------
    user_message : str
        Raw user input text (already classified as 'action' by the intent classifier).

    Returns
    -------
    Dict[str, Any]
        {
          "action_type": str,
          "action_confidence": float,
          "action_details": str,
        }
    """
    prompt = SUBACTION_ROUTER_PROMPT.replace("{user_message}", user_message)

    messages = [{"role": "user", "content": prompt}]
    response = _llm_wrapper.invoke(messages).strip()

    parsed = _extract_json_block(response)

    action_type = parsed.get("action_type", "unknown")
    try:
        action_confidence = float(parsed.get("action_confidence", 0.8))
    except Exception:
        action_confidence = 0.0
    action_details = parsed.get("action_details", "")

    if not parsed:
        action_type = "unknown"
        action_confidence = 0.0
        action_details = "No JSON found or invalid LLM output."

    # Confidence / ambiguity handling
    if (not action_type) or (action_confidence < 0.6) or (action_type == "unknown"):
        action_type = "unknown"
        action_details = "Action type ambiguous or unavailable. Please clarify."

    return {
        "action_type": action_type,
        "action_confidence": action_confidence,
        "action_details": action_details,
    }


if __name__ == "__main__":
    while True:
        text = input("Action command (type 'exit' to quit): ")
        if text.strip().lower() == "exit":
            break
        print(route_action_message(text))