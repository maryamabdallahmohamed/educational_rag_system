from backend.retrievers.supabase_store import create_conversation, log_message
import uuid

def init_conversation_node(state: dict) -> dict:
    if "conversation_id" not in state:
        # Always create a conversation in the DB and use its ID
        state["conversation_id"] = create_conversation()
    return state

def chatbot_node(state: dict) -> dict:
    strategy = state.get("strategy", "default")
    answer = state.get("answer", "")

    query = state.get("query") if strategy == "chat" else " "

    conversation_id = state.get("conversation_id")

    state["conversation_id"] = conversation_id

    log_message(conversation_id=conversation_id, query=query, answer=answer, strategy=state.get('task_choice'))
    return state

