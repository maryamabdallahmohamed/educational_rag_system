from backend.core.graph_states import RAGState
from backend.retrievers.supabase_store import chunk_store ,doc_store

def db_add_node(state: RAGState) -> RAGState:
    chunk_store.add_documents(state["chunks"])
    doc_store.add_documents(state["documents"])
    state["vectorstore"] = chunk_store
    return state
