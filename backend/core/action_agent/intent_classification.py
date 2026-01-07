import re
import json
from typing import Dict, Any

from backend.core.action_agent.prompts import MAIN_INTENT_PROMPT
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


def classify_intent_message(user_message: str) -> Dict[str, Any]:
    """
    Classify a user message as 'action' or 'query' using MAIN_INTENT_PROMPT.

    Parameters
    ----------
    user_message : str
        Raw user input text.

    Returns
    -------
    Dict[str, Any]
        {
          "intent_type": "action" | "query",
          "intent_confidence": float,
          "intent_details": str | dict,
        }
    """
    # Build prompt
    prompt = MAIN_INTENT_PROMPT.replace("{user_message}", user_message)

    # GroqLLM expects List[dict] messages
    messages = [{"role": "user", "content": prompt}]
    response = _llm_wrapper.invoke(messages).strip()

    parsed = _extract_json_block(response)

    intent_type = parsed.get("intent_type", "query")
    try:
        intent_confidence = float(parsed.get("intent_confidence", 0.8))
    except Exception:
        intent_confidence = 0.0
    intent_details = parsed.get("intent_details", "")

    if not parsed:
        intent_type = "query"
        intent_confidence = 0.0
        intent_details = "No JSON found or invalid LLM output."

    # Confidence threshold + ambiguity handling
    if not intent_type or intent_confidence < 0.6:
        intent_type = "query"
        intent_details = (
            "Intent was ambiguous. Routed to general chat for user clarification."
        )

    return {
        "intent_type": intent_type,
        "intent_confidence": intent_confidence,
        "intent_details": intent_details,
    }

