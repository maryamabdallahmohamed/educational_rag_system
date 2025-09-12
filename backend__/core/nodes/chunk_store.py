import json
from backend__.core.states.graph_states import RAGState
from backend__.models.embedders.hf_embedder import HFEmbedder
from backend__.loaders.document_loaders.text_splitter import document_chunk
from backend__.utils.helpers.language_detection import returnlang
from backend__.db.connect_db import run_query
from langchain.schema import Document

embedder_model = HFEmbedder()

def chunk_and_store_node(state: RAGState) -> RAGState:
    new_docs = state.get("new_documents") or []
    if not new_docs:
        return state

    inserted_doc_ids = []
    all_chunks = []

    for doc in new_docs:

        embedding = embedder_model.embed_query(doc.page_content)
        metadata_json = json.dumps(doc.metadata or {})

        query = """
            INSERT INTO documents (title, content, metadata, embedding)
            VALUES (%s, %s, %s::jsonb, %s::vector)
            RETURNING id
        """
        params = (
            (doc.metadata or {}).get("title"),
            doc.page_content,
            metadata_json,
            embedding,
        )

        resp = run_query(query, params, fetch=True)
        if not resp:
            raise RuntimeError("Document insert failed — no id returned")
        doc_id = resp[0][0]
        print(f'resp is {resp}')
        inserted_doc_ids.append(doc_id)

        chunks = document_chunk(doc.page_content)
        for i, chunk in enumerate(chunks):
            chunk_doc = Document(
                page_content=chunk,
                metadata={**(doc.metadata or {}), "chunk_id": i, "language": returnlang(chunk)},
            )
            all_chunks.append((chunk_doc, doc_id))


    for chunk_doc, doc_id in all_chunks:
        embedding = embedder_model.embed_query(chunk_doc.page_content)
        metadata_json = json.dumps(chunk_doc.metadata or {})

        query = """
            INSERT INTO chunks (document_id, content, metadata, embedding)
            VALUES (%s, %s, %s::jsonb, %s::vector)
        """
        params = (doc_id, chunk_doc.page_content, metadata_json, embedding)
        run_query(query, params, fetch=False)

    state["new_chunks"] = (state.get("new_chunks") or []) + [c for c, _ in all_chunks]
    state["document_ids"] = inserted_doc_ids
    return state
