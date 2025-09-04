from backend.core.graph_states import RAGState
from backend.loaders.base import document_chunk
from langchain.schema import Document
from backend.utils.language_detection import returnlang

def chunk_node(state: RAGState) -> RAGState:
    if "documents" not in state or not state["documents"]:
        print("⚠️ No documents to chunk. Skipping.")
        return state
    
    all_chunks = []
    for doc in state["documents"]:
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
    state["chunks"] = all_chunks
    return state