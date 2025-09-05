from backend.core.graph_states import RAGState
from backend.models.embedders.hf_embedder import HFEmbedder
from langchain.schema import Document
from backend.retrievers.supabase_store import supabase, chunk_store, doc_store

embedder_model = HFEmbedder()

def db_add_node(state: RAGState) -> RAGState:
    """
    Insert documents & chunks into Supabase (SQL client for writes).
    Retrieval remains powered by SupabaseVectorStore.
    """
    new_documents = state.get("new_documents") or []
    new_chunks = state.get("new_chunks") or []

    inserted_doc_ids = []

    # 1. Insert documents
    for doc in new_documents:
        if not isinstance(doc, Document):
            raise TypeError(f"Expected Document, got {type(doc)}")

        embedding = embedder_model.embed_query(doc.page_content)

        resp = supabase.table("documents").insert({
            "title": doc.metadata.get("title"),
            "content": doc.page_content,
            "metadata": doc.metadata or {},
            "embedding": embedding,
        }).execute()

        doc_id = resp.data[0]["id"]
        inserted_doc_ids.append(doc_id)

    # 2. Insert chunks (link to documents)
    for idx, chunk in enumerate(new_chunks):
        if not isinstance(chunk, Document):
            raise TypeError(f"Expected Document for chunk, got {type(chunk)}")

        document_id = inserted_doc_ids[idx % len(inserted_doc_ids)] if inserted_doc_ids else None
        if not document_id:
            raise ValueError("❌ Cannot insert chunk without a document_id")

        embedding = embedder_model.embed_query(chunk.page_content)

        supabase.table("chunks").insert({
            "document_id": document_id,
            "content": chunk.page_content,
            "metadata": chunk.metadata or {},
            "embedding": embedding,
        }).execute()

    # 3. Update state
    if new_chunks:
        state["vectorstore"] = chunk_store  # retrieval stays via vectorstore
    if inserted_doc_ids:
        state["document_ids"] = inserted_doc_ids

    return state
