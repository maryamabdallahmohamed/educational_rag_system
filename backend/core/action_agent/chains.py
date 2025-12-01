from typing import Dict, Any, Callable
from langchain_core.runnables import RunnableLambda

from backend.core.action_agent.intent_classification import classify_intent_message
from backend.core.action_agent.query_router import route_query_message
from backend.core.action_agent.action_router import route_action_message

from backend.core.action_agent.handlers.dispatchers import dispatch_action, dispatch_query

#-----------------------------
# Chain functions
#-----------------------------
def _intent_chain_fn(inputs: Dict[str, Any]) -> Dict[str, Any]:
    user_message: str = inputs["user_message"]
    return classify_intent_message(user_message)

def _query_router_chain_fn(inputs: Dict[str, Any]) -> Dict[str, Any]:
    user_message: str = inputs["user_message"]
    return route_query_message(user_message)

def _action_router_chain_fn(inputs: Dict[str, Any]) -> Dict[str, Any]:
    user_message: str = inputs["user_message"]
    return route_action_message(user_message)

#-----------------------------
# Individual chains
#-----------------------------
INTENT_CHAIN = RunnableLambda(_intent_chain_fn)
QUERY_ROUTER_CHAIN = RunnableLambda(_query_router_chain_fn)
ACTION_ROUTER_CHAIN = RunnableLambda(_action_router_chain_fn)

#-----------------------------
# Full router chain
#-----------------------------
def _full_router_logic(inputs: Dict[str, Any]) -> Dict[str, Any]:
    user_message: str = inputs["user_message"]
    dispatch_action: Callable | None = inputs.get("dispatch_action")
    dispatch_query: Callable | None = inputs.get("dispatch_query")

    intent = classify_intent_message(user_message)

    result: Dict[str, Any] = {
        "user_message": user_message,
        "intent": intent,
        "query_route": None,
        "action_route": None,
        "dispatch_result": None,
    }

    if intent["intent_type"] == "query":
        q_route = route_query_message(user_message)
        result["query_route"] = q_route

        if dispatch_query is not None:
            result["dispatch_result"] = dispatch_query(
                {
                    "user_message": user_message,
                    **q_route,
                }
            )

    elif intent["intent_type"] == "action":
        a_route = route_action_message(user_message)
        result["action_route"] = a_route

        if dispatch_action is not None:
            result["dispatch_result"] = dispatch_action(
                {
                    "user_message": user_message,
                    **a_route,
                }
            )

    return result

FULL_ROUTER_CHAIN = RunnableLambda(_full_router_logic)