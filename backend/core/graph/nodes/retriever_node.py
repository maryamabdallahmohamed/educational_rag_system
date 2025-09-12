from backend.core.graph.states.graph_states import RAGState
from backend.data.stores.supabase_store import chunk_store
from backend__.config import GLOBAL_K

def retrieve_node(state: RAGState) -> RAGState:
    vectorstore = state["vectorstore"]  
    results =chunk_store.similarity_search(state["query"], k=GLOBAL_K)
    state["results"] = results
    return state
