from backend.core.graph_states import RAGState
def router_node(state: RAGState) -> RAGState:
    """
    Determines the user-selected task:
    - "chat":chat with thedocuments
    - "generate_summary": generate detailed summary
    - "qa": question-answering
    """
    # Assume state["task_choice"] comes from the frontend/user input
    task_choice = state.get("task_choice", "").lower()

    if task_choice not in ["summarize", "chat", "qa"]:
        # Default fallback
        state["route"] = "chat"
    else:
        state["route"] = task_choice

    return state
