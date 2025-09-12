
from langgraph.graph import StateGraph, START, END
from backend.core.graph.states.graph_states import RAGState
from backend__.core.nodes.loader import load_node
from backend__.core.nodes.chunk_store import chunk_and_store_node
from backend.core.graph.nodes.router import router_node
from backend.core.graph.nodes.db_nodes.nodes import init_conversation_node, chatbot_node
from backend.core.stratgies.chat import chat_node
from backend.core.graph.nodes.cpa_tools.qa_generator import QA
from backend.core.graph.nodes.cpa_tools.summarizer import summary_node
def router_decision(state: RAGState) -> str:
    """Decide which node to route to based on task choice."""
    routes = {
        "summarize": "summarise",

        "summarise": "summarise",
        "qa": "QA",
        "question_answer": "QA",
        "chat": "chat",
    }
    return routes.get(state.get("task_choice", "").lower(), "chat")

def should_ingest(state: RAGState) -> str:
    """Decide whether to run ingestion based on new file paths not yet seen."""
    file_paths = state.get("file_paths") or []
    seen = set(state.get("ingested_sources") or [])
    new_paths = [p for p in file_paths if p not in seen]
    return "ingest" if len(new_paths) > 0 else "router"


def mark_ingested_node(state: RAGState) -> RAGState:
    """Update state to mark any provided file_paths as ingested and merge new docs/chunks."""
    file_paths = state.get("file_paths") or []
    already = set(state.get("ingested_sources") or [])
    updated = list(already.union(file_paths))
    state["ingested_sources"] = updated
    # Merge newly produced docs/chunks into persistent lists
    if state.get("new_documents"):
        docs = state.get("documents") or []
        docs.extend(state["new_documents"]) 
        state["documents"] = docs
        state.pop("new_documents", None)
    if state.get("new_chunks"):
        chunks = state.get("chunks") or []
        chunks.extend(state["new_chunks"]) 
        state["chunks"] = chunks
        state.pop("new_chunks", None)
    state["ingested"] = True
    return state


def build_rag_graph():
    """Build and compile the RAG graph with conditional ingestion and logging."""
    graph = StateGraph(RAGState)


    graph.add_node("init_conversation", init_conversation_node)
    graph.add_node("chatbot", chatbot_node)

    # Ingestion nodes
    graph.add_node("load", load_node)
    graph.add_node("db and store", chunk_and_store_node)
    graph.add_node("mark_ingested", mark_ingested_node)

    # Query nodes
    graph.add_node("router", router_node)
    graph.add_node("chat", chat_node)
    graph.add_node("QA", QA)
    graph.add_node("summarise", summary_node)

  
    graph.add_conditional_edges(
        START,
        should_ingest,
        {
            "ingest": "load",
            "router": "router",
        },
    )

    # Ingestion chain
    graph.add_edge("load", "db and store")
    graph.add_edge("db and store", "mark_ingested")
    graph.add_edge("mark_ingested", "router")

    # Router → Query handlers
    graph.add_conditional_edges(
        "router",
        router_decision,
        {
            "chat": "init_conversation",
            "QA": "init_conversation",
            "summarise": "init_conversation",
        },
    )

    # Conversation init → handler
    graph.add_conditional_edges(
        "init_conversation",
        router_decision,   # reuse router_decision to branch again
        {
            "chat": "chat",
            "QA": "QA",
            "summarise": "summarise",
        },
    )

    # After handler → log message
    graph.add_edge("chat", "chatbot")
    graph.add_edge("QA", "chatbot")
    graph.add_edge("summarise", "chatbot")

    # ✅ End state
    graph.add_edge("chatbot", END)

    return graph.compile()


app= build_rag_graph()
if __name__ == "__main__":
    print("🟢 Welcome to the RAG Chatbot! Type 'exit' to quit.\n")

    # Initialize persistent state
    state = RAGState(documents=[], task_choice="QA")

    # Optionally load documents
    file_paths = input("Enter file paths separated by commas (or leave empty): ").strip()
    if file_paths:
        state["file_paths"] = [fp.strip() for fp in file_paths.split(",")]

    def run_chat_loop(state: RAGState):
        """Main interactive chat loop with persistent memory."""
        while True:
            query = input("\nYou: ").strip()
            if query.lower() == "exit":
                print("👋 Goodbye!")
                break

            state["query"] = query
            try:
                state = app.invoke(state)  # preserve memory
                print("Assistant:", state.get("answer", "⚠️ No answer"))
            except Exception as e:
                print(f"❌ Error: {e}")
        return state

    # Start interactive session
    state = run_chat_loop(state)

