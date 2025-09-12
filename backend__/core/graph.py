
from langgraph.graph import StateGraph, START, END
from backend__.core.states.graph_states import RAGState
from backend__.core.nodes.loader import load_node
from backend__.core.nodes.chunk_store import chunk_and_store_node
def build_rag_graph():
    """Build and compile the RAG graph with conditional ingestion and logging."""
    graph = StateGraph(RAGState)
    graph.add_node("loader",load_node)
    graph.add_node("chunk and store",chunk_and_store_node)

    graph.add_edge(START,"loader")
    graph.add_edge("loader","chunk and store")
    graph.add_edge("chunk and store",END)


    return graph.compile()


app= build_rag_graph()
# if __name__ == "__main__":
#     print("🟢 Welcome to the RAG Chatbot! Type 'exit' to quit.\n")

#     # Initialize persistent state
#     state = RAGState(documents=[], task_choice="QA")

#     # Optionally load documents
#     file_paths = input("Enter file paths separated by commas (or leave empty): ").strip()
#     if file_paths:
#         state["file_paths"] = [fp.strip() for fp in file_paths.split(",")]

#     def run_chat_loop(state: RAGState):
#         """Main interactive chat loop with persistent memory."""
#         while True:
#             query = input("\nYou: ").strip()
#             if query.lower() == "exit":
#                 print("👋 Goodbye!")
#                 break

#             state["query"] = query
#             try:
#                 state = app.invoke(state)  # preserve memory
#                 print("Assistant:", state.get("answer", "⚠️ No answer"))
#             except Exception as e:
#                 print(f"❌ Error: {e}")
#         return state

#     # Start interactive session
#     state = run_chat_loop(state)

