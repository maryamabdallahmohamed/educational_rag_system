import json
from backend__.core.states.graph_states import RAGState
from backend__.utils.helpers.language_detection import returnlang
from backend__.loaders.document_loaders.text_splitter import document_chunk
from langchain.schema import Document
from backend__.utils.logger_config import get_logger
from backend__.models.embedders.hf_embedder import HFEmbedder
from backend__.db.connect_db import run_query


class ChunkAndStoreNode:
    def __init__(self):
        self.embedder = HFEmbedder()
        self.db_runner = run_query
        self.logger =get_logger('chunk_and_store')

    def _insert_document(self, doc: Document):
        embedding = self.embedder.embed_query(doc.page_content)
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
        resp = self.db_runner(query, params, fetch=True)
        if not resp:
            raise RuntimeError("Document insert failed — no id returned")
        return resp[0][0]

    def _insert_chunk(self, chunk_doc: Document, doc_id: int):
        embedding = self.embedder.embed_query(chunk_doc.page_content)
        metadata_json = json.dumps(chunk_doc.metadata or {})

        query = """
            INSERT INTO chunks (document_id, content, metadata, embedding)
            VALUES (%s, %s, %s::jsonb, %s::vector)
        """
        params = (doc_id, chunk_doc.page_content, metadata_json, embedding)
        # self.db_runner(query, params, fetch=False)

    def process(self, state: RAGState) -> RAGState:
        new_docs = state.get("new_documents") or []
        if not new_docs:
            return state

        inserted_doc_ids = []
        all_chunks = []

        for doc in new_docs:
            doc_id = self._insert_document(doc)
            inserted_doc_ids.append(doc_id)

            chunks = document_chunk(doc.page_content)
            for i, chunk in enumerate(chunks):
                chunk_doc = Document(
                    page_content=chunk,
                    metadata={**(doc.metadata or {}), "chunk_id": i, "language": returnlang(chunk)},
                )
                all_chunks.append((chunk_doc, doc_id))

        for chunk_doc, doc_id in all_chunks:
            self._insert_chunk(chunk_doc, doc_id)

        state["new_chunks"] = [c for c, _ in all_chunks]
        state["document_ids"] = inserted_doc_ids


        self.logger.info("Inserted %d documents and %d chunks", len(inserted_doc_ids), len(all_chunks))

        return state




