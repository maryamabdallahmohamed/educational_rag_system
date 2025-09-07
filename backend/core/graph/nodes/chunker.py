from backend.core.graph.states.graph_states import RAGState
from backend.loaders.document_loaders.base import document_chunk
from langchain.schema import Document
from backend.utils.helpers.language_detection import returnlang

def chunk_node(state: RAGState) -> RAGState:
    new_docs = state.get("new_documents") or []
    if not new_docs:
        return state

    all_chunks = []
    for doc in new_docs:
        chunks = document_chunk(doc.page_content)
        for i, chunk in enumerate(chunks):
            chunk_doc = Document(
                page_content=chunk,
                metadata={
                    **doc.metadata,  
                    "chunk_id": i,
                    'language': returnlang(chunk)
                }
            )
            all_chunks.append(chunk_doc)
    state["new_chunks"] = (state.get("new_chunks") or []) + all_chunks
    return state