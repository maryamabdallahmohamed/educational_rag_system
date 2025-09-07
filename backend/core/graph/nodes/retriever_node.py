from backend.core.graph.states.graph_states import RAGState
from backend.data.stores.supabase_store import chunk_store


def retrieve_node(state: RAGState) -> RAGState:
    vectorstore = state["vectorstore"]  
    results =chunk_store.similarity_search(state["query"], k=3)
    state["results"] = results
    return state
