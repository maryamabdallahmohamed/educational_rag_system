from backend.core.graph_states import RAGState
from backend.retrievers.supabase_store import chunk_store, doc_store

def db_add_node(state: RAGState) -> RAGState:
    """
    DB add node:
    - Adds chunks to the chunk_store if available
    - Adds documents to the doc_store if available
    - Updates state with the vectorstore reference
    """
    chunks = state.get("chunks", [])
    documents = state.get("documents", [])

    if chunks:
        chunk_store.add_documents(chunks)
        state["vectorstore"] = chunk_store  

    if documents:
        doc_store.add_documents(documents)

    return state
