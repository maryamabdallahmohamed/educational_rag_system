from langgraph.graph import StateGraph, START, END
from backend.core.graph_states import RAGState
from backend.core.nodes.loader import load_node
from backend.core.nodes.chunker import chunk_node
from backend.core.nodes.db_loader import db_add_node
from backend.core.nodes.router import router_node
from backend.core.stratgies.chat import chat_node
from backend.core.stratgies.qa_generator import QA
from langgraph.types import RunnableConfig
from backend.core.stratgies.summarizer import summary_node


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


def build_rag_graph():
    """Build and compile the RAG graph with memory."""
    graph = StateGraph(RAGState)

    # Add nodes
    graph.add_node("load", load_node)
    graph.add_node("chunk", chunk_node)
    graph.add_node("db", db_add_node)
    graph.add_node("router", router_node)
    graph.add_node("chat", chat_node)
    graph.add_node("QA", QA)
    graph.add_node("summarise", summary_node)
    

    # Add edges
    graph.add_edge(START, "load")
    graph.add_edge("load", "chunk")
    graph.add_edge("chunk", "db")
    graph.add_edge("db", "router")

    # Conditional routing
    graph.add_conditional_edges(
        "router",
        router_decision,
        {
            "chat": "chat",
            "QA": "QA",
            "summarise": "summarise",
        }
    )

    # End edges
    graph.add_edge("chat", END)
    graph.add_edge("QA", END)
    graph.add_edge("summarise", END)

    # Compile with memory
    return graph.compile()


# Create the compiled graph
app = build_rag_graph()

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

