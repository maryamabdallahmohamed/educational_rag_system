"""
query_router.py

Backend-ready query router using SUBQUERY_ROUTER_PROMPT.
Classifies a query into: "qa", "summarization", or "content_processor_agent".
"""

import os
import re
import json
from typing import Dict, Any

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

from prompts import SUBQUERY_ROUTER_PROMPT

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Initialize LLM
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=groq_api_key,
)

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


def route_query_message(
    user_message: str,
    llm_client: ChatGroq | None = None,
) -> Dict[str, Any]:
    """
    Route a query into one of: "qa", "summarization", "content_processor_agent".

    Parameters
    ----------
    user_message : str
        Raw user input text.
    llm_client : ChatGroq | None
        Optional injected LLM client.

    Returns
    -------
    Dict[str, Any]
        {
          "route": "qa" | "summarization" | "content_processor_agent",
          "route_confidence": float,
          "route_details": str,
        }
    """
    client = llm_client or llm

    # Build prompt
    prompt = SUBQUERY_ROUTER_PROMPT.replace("{user_message}", user_message)

    # Call LLM
    response = client.invoke([HumanMessage(content=prompt)]).content.strip()

    # Parse JSON
    parsed = _extract_json_block(response)

    route = parsed.get("route", "content_processor_agent")
    try:
        route_confidence = float(parsed.get("route_confidence", 0.8))
    except Exception:
        route_confidence = 0.0
    route_details = parsed.get("route_details", "")

    if not parsed:
        route = "content_processor_agent"
        route_confidence = 0.0
        route_details = "No JSON found or invalid LLM output."

    # Confidence / ambiguity handling
    if not route or route_confidence < 0.6:
        route = "content_processor_agent"
        route_details = "Query type ambiguous. Routed to general chat."

    return {
        "route": route,
        "route_confidence": route_confidence,
        "route_details": route_details,
    }


if __name__ == "__main__":
    # Simple manual test
    while True:
        text = input("Query (type 'exit' to quit): ")
        if text.strip().lower() == "exit":
            break

        result = route_query_message(text)
        print(result)