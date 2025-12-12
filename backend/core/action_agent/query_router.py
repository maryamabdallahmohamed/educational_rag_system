"""
query_router.py

Backend-ready query router using SUBQUERY_ROUTER_PROMPT and GroqLLM.
Classifies a query into: "qa", "summarization", or "content_processor_agent".
"""

import re
import json
from typing import Dict, Any
from backend.core.action_agent.prompts import SUBQUERY_ROUTER_PROMPT
from backend.models.llms.ollama_llm import OllamaLLM  # adjust path if needed
from backend.utils.logger_config import get_logger
logger = get_logger("query_router")
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


def route_query_message(user_message: str) -> Dict[str, Any]:
    """
    Route a query into one of: "qa", "summarization", "content_processor_agent".

    Parameters
    ----------
    user_message : str
        Raw user input text.

    Returns
    -------
    Dict[str, Any]
        {
          "route": "qa" | "summarization" | "content_processor_agent",
          "route_confidence": float,
          "route_details": str,
        }
    """
    logger.info(f"Routing query: {user_message}")
    prompt = SUBQUERY_ROUTER_PROMPT.replace("{user_message}", user_message)

    messages = [{"role": "user", "content": prompt}]
    response = _llm_wrapper.invoke(messages).strip()

    parsed = _extract_json_block(response)
    logger.info(f"Parsed response: {parsed}")

    route = parsed.get("route", "content_processor_agent")
    logger.info(f"Route: {route}")
    try:
        route_confidence = float(parsed.get("route_confidence", 0.8))
        logger.info(f"Route confidence: {route_confidence}")
    except Exception:
        route_confidence = 0.0
    route_details = parsed.get("route_details", "")
    logger.info(f"Route details: {route_details}")

    if not parsed:
        route = "content_processor_agent"
        route_confidence = 0.0
        route_details = "No JSON found or invalid LLM output."
        logger.info(f"Routed to general chat due to no JSON found or invalid LLM output.")

    # Confidence / ambiguity handling
    if not route or route_confidence < 0.6:
        route = "content_processor_agent"
        route_details = "Query type ambiguous. Routed to general chat."
        logger.info(f"Routed to general chat due to low confidence or ambiguous query type.")

    return {
        "route": route,
        "route_confidence": route_confidence,
        "route_details": route_details,
    }


